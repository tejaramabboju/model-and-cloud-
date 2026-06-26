"""
Extractor service — uses Google Gemini to extract 20 structured fields
from a use case description + optional structured form input.
Form fields always take priority over LLM-extracted values.
"""

import asyncio
import json
import logging
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """
You are an expert AI infrastructure analyst. Your job is to extract ALL
structured requirements from the user's input — a mix of a free-text
description AND optionally structured form fields the user filled in.

Extract the following fields. If the user explicitly provided a value in the
form, use it directly. If they left it blank or said "not sure / skip", set
the value to "unknown" — never guess for unknown fields.

FIELDS TO EXTRACT:

1.  project_name          — Short name for the project (string, "unknown" if missing)
2.  task_type             — Primary AI task:
                            classification | summarization | content_generation |
                            chat | extraction | translation | code_generation |
                            search | recommendation | image_analysis |
                            speech_to_text | anomaly_detection | forecasting |
                            document_processing | multimodal | other
3.  industry              — Industry vertical:
                            healthcare | finance | legal | ecommerce | education |
                            manufacturing | telecom | media | government | hr |
                            retail | logistics | saas | other | unknown
4.  data_sensitivity      — Sensitivity of data handled:
                            none | low | medium | high | critical
                            Criteria:
                              none     = public data only
                              low      = internal business data, no PII
                              medium   = some PII (names, emails)
                              high     = financial, regulated PII
                              critical = PHI (health), classified, HIPAA-scope
5.  compliance_region     — Regulatory geography:
                            EU | USA | India | UK | Australia | Canada |
                            global | none | unknown
6.  compliance_standards  — Specific standards required (list, empty [] if none):
                            GDPR | HIPAA | SOC2 | PCI_DSS | ISO27001 |
                            FedRAMP | DPDP | none
7.  daily_requests        — Estimated requests per day as a string number (e.g. "5000") or "unknown"
8.  avg_input_tokens      — Avg input tokens per request as a string number or "unknown"
9.  avg_output_tokens     — Avg output tokens per request as a string number or "unknown"
10. monthly_budget_usd    — Max monthly budget in USD as a number, or null if unknown
11. latency_requirement   — Max acceptable latency:
                            realtime_100ms | fast_1s | moderate_5s | batch | unknown
12. existing_cloud        — Cloud provider already in use (AWS | GCP | Azure | none | unknown)
13. existing_services     — Other tech already in use (list of strings, [] if unknown)
14. team_expertise        — Team's cloud/AI experience level:
                            beginner | intermediate | expert | unknown
15. multimodal_needs      — Does the use case need image, audio, or video? (true | false | null)
16. streaming_needed      — Does the response need to stream token-by-token? (true | false | null)
17. fine_tuning_needed    — Is custom fine-tuning required? (true | false | null)
18. on_premise_required   — Must data stay on-premise or private VPC? (true | false | null)
19. high_availability     — Is 99.9%+ uptime required? (true | false | null)
20. description_summary   — 1-2 sentence plain-English summary of what the user wants to build

Also include these legacy fields for backward compatibility:
  scale_volume: "low (<1K/day)" | "medium (1K-100K/day)" | "high (>100K/day)" | "unknown"
  latency_need: human-friendly latency description string
  budget_hint: human-friendly budget string

Return ONLY valid JSON with these exact keys. No markdown, no explanation.
"""

_DEFAULTS: dict = {
    "project_name": "unknown",
    "task_type": "unknown",
    "industry": "unknown",
    "data_sensitivity": "none",
    "compliance_region": "unknown",
    "compliance_standards": [],
    "daily_requests": "unknown",
    "avg_input_tokens": "unknown",
    "avg_output_tokens": "unknown",
    "monthly_budget_usd": None,
    "latency_requirement": "unknown",
    "existing_cloud": "none",
    "existing_services": [],
    "team_expertise": "unknown",
    "multimodal_needs": None,
    "streaming_needed": None,
    "fine_tuning_needed": None,
    "on_premise_required": None,
    "high_availability": None,
    "description_summary": "",
    # legacy
    "scale_volume": "unknown",
    "latency_need": "unknown",
    "budget_hint": "unknown",
}


def _merge_form_fields(extracted: dict, form_fields: dict | None) -> dict:
    """
    Merge user-provided structured form fields into the LLM-extracted dict.
    Form fields always override LLM extraction when they are not None/unknown.
    """
    if not form_fields:
        return extracted

    result = dict(extracted)

    field_map = {
        "project_name": "project_name",
        "daily_requests": "daily_requests",
        "avg_input_tokens": "avg_input_tokens",
        "avg_output_tokens": "avg_output_tokens",
        "monthly_budget_usd": "monthly_budget_usd",
        "number_of_users": "number_of_users",
        "data_sensitivity": "data_sensitivity",
        "compliance_region": "compliance_region",
        "compliance_standards": "compliance_standards",
        "existing_cloud": "existing_cloud",
        "team_expertise": "team_expertise",
        "streaming_needed": "streaming_needed",
        "fine_tuning_needed": "fine_tuning_needed",
        "on_premise_required": "on_premise_required",
        "multimodal_needs": "multimodal_needs",
        "high_availability": "high_availability",
    }

    for form_key, extracted_key in field_map.items():
        val = form_fields.get(form_key)
        if val is None:
            continue
        if isinstance(val, str) and val.lower() in ("unknown", "skip", ""):
            continue
        if isinstance(val, list) and len(val) == 0:
            continue
        result[extracted_key] = val

    # Keep legacy fields in sync
    if result.get("monthly_budget_usd"):
        budget = result["monthly_budget_usd"]
        if budget < 200:
            result["budget_hint"] = f"low (~${budget}/month)"
        elif budget < 2000:
            result["budget_hint"] = f"moderate (~${budget}/month)"
        else:
            result["budget_hint"] = f"enterprise (~${budget}/month)"

    if result.get("daily_requests") and result["daily_requests"] != "unknown":
        try:
            dr = int(str(result["daily_requests"]).replace(",", ""))
            if dr < 1000:
                result["scale_volume"] = "low (<1K/day)"
            elif dr < 100_000:
                result["scale_volume"] = "medium (1K-100K/day)"
            else:
                result["scale_volume"] = "high (>100K/day)"
        except (ValueError, TypeError):
            pass

    return result


async def extract_fields(description: str, form_fields: dict | None = None) -> dict:
    """
    Extract 20 structured fields from a use case description using Gemini.
    If form_fields are provided, they take priority over LLM extraction.
    Falls back to defaults if the API call or JSON parsing fails.
    """
    settings = get_settings()
    api_key = settings.GEMINI_API_KEY

    if not api_key or "gemini-key" in api_key or "your-key" in api_key:
        logger.warning("Gemini API key not configured. Using defaults + form fields.")
        return _merge_form_fields({**_DEFAULTS}, form_fields)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    form_context = ""
    if form_fields:
        non_empty = {k: v for k, v in form_fields.items() if v is not None}
        if non_empty:
            form_context = f"\n\nThe user also provided these structured form fields (use these directly for the corresponding extracted fields):\n{json.dumps(non_empty, indent=2)}"

    payload = {
        "contents": [{
            "parts": [{
                "text": f"Extract fields from this use case description:{form_context}\n\nDescription:\n{description}"
            }]
        }],
        "systemInstruction": {
            "parts": [{"text": EXTRACTION_SYSTEM_PROMPT}]
        },
        "generationConfig": {"responseMimeType": "application/json"},
    }

    max_retries = 3
    retry_delay = 1.0
    response = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=15.0)
                if response.status_code == 200:
                    break
                elif response.status_code in (429, 503) and attempt < max_retries - 1:
                    logger.warning("Gemini API %s for extraction. Retry in %ss...", response.status_code, retry_delay)
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2.0
                else:
                    response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            if attempt < max_retries - 1:
                logger.warning("Network error during extraction: %s. Retry...", e)
                await asyncio.sleep(retry_delay)
                retry_delay *= 2.0
            else:
                logger.error("All retries failed during extraction: %s", e)
                return _merge_form_fields({**_DEFAULTS}, form_fields)
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error during extraction: %s", e)
            return _merge_form_fields({**_DEFAULTS}, form_fields)
        except Exception as e:
            logger.error("Unexpected error during extraction: %s", e)
            return _merge_form_fields({**_DEFAULTS}, form_fields)

    try:
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        extracted = json.loads(raw_text)
        result = {**_DEFAULTS, **extracted}
        return _merge_form_fields(result, form_fields)

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning("Failed to parse extraction JSON: %s", e)
        return _merge_form_fields({**_DEFAULTS}, form_fields)
    except Exception as e:
        logger.error("Unexpected error parsing extraction: %s", e)
        return _merge_form_fields({**_DEFAULTS}, form_fields)
