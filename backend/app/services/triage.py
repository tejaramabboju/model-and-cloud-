"""
Triage service — classifies use case complexity and detects missing critical info
that would require clarification before generating a high-confidence recommendation.
"""

import asyncio
import json
import logging
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

TRIAGE_SYSTEM_PROMPT = """
You are an expert AI use-case complexity classifier.

Given a use case description and extracted fields, classify complexity as
Simple, Moderate, or Complex AND identify whether additional information
is needed before a high-confidence recommendation can be made.

CLASSIFICATION CRITERIA:

Simple:
  - Straightforward tasks: FAQ, basic chat, email categorization, simple extraction
  - No PII or sensitive data
  - No compliance requirements
  - Low accuracy stakes
  - Token usage: predictable, low volume

Moderate:
  - Meaningful reasoning, some PII, or regulatory requirements
  - GDPR or similar soft compliance
  - Customer-facing with moderate accuracy needs
  - Medium token usage or unclear volume

Complex:
  - High-stakes: medical, legal, financial, fraud detection
  - PHI, critical PII, HIPAA / FedRAMP / PCI-DSS
  - Real-time with <100ms latency constraints
  - Fine-tuning, multimodal, or on-premise required
  - Missing budget or volume makes cost estimation unreliable

CLARIFICATION DETECTION:
Identify whether any critical information is missing that would significantly
change the recommendation. Flag each missing field with a user-friendly question.

Critical missing fields that trigger a clarification question:
  - daily_requests = "unknown"        → "How many requests per day do you expect? (Under 1K / 1K-10K / 10K-100K / Over 100K)"
  - monthly_budget_usd = null and budget_hint = "unknown"  → "What is your approximate monthly budget for AI infrastructure (USD)?"
  - compliance_region = "unknown" AND data_sensitivity is medium/high/critical  → "Which country or region will your users be in? (EU / USA / India / UK / other)"
  - data_sensitivity = "none" but industry is healthcare/finance/legal  → "Will your system process patient records, financial data, or legal documents?"
  - avg_input_tokens = "unknown" AND task_type involves long documents  → "How long are the documents or inputs you'll process? (Short <200 words / Medium 1-5 pages / Long 5-20 pages / Very long 20+ pages)"

IMPORTANT: Only ask for clarification if the missing info would materially change the recommendation (e.g., switch from one model tier to another, or change compliance setup). Do NOT ask for clarification for cosmetic or minor details.

Return ONLY valid JSON:
{
  "classification": "Simple|Moderate|Complex",
  "reasoning": "Brief explanation (2-3 sentences)",
  "needs_clarification": true or false,
  "clarification_questions": [
    "Question 1 for the user?",
    "Question 2 for the user?"
  ]
}

If needs_clarification is false, return an empty list for clarification_questions.
Maximum 3 clarification questions.
"""


async def classify_complexity(description: str, extracted_fields: dict) -> dict:
    """
    Classify the complexity of a use case using Gemini.
    Falls back to 'Moderate' with no clarification on failure.
    """
    settings = get_settings()
    api_key = settings.GEMINI_API_KEY

    _fallback = {
        "classification": "Moderate",
        "reasoning": "Triage defaulted to Moderate because the API key is not configured.",
        "needs_clarification": False,
        "clarification_questions": [],
    }

    if not api_key or "gemini-key" in api_key or "your-key" in api_key:
        logger.warning("Gemini API key not configured. Defaulting triage to Moderate.")
        # Still run local clarification check
        return _local_clarification_check(extracted_fields, _fallback)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    user_content = (
        f"Use case description:\n{description}\n\n"
        f"Extracted fields:\n{json.dumps(extracted_fields, indent=2)}"
    )

    payload = {
        "contents": [{"parts": [{"text": user_content}]}],
        "systemInstruction": {"parts": [{"text": TRIAGE_SYSTEM_PROMPT}]},
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
                    logger.warning("Gemini API %s for triage. Retry in %ss...", response.status_code, retry_delay)
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2.0
                else:
                    response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            if attempt < max_retries - 1:
                logger.warning("Network error during triage: %s. Retry...", e)
                await asyncio.sleep(retry_delay)
                retry_delay *= 2.0
            else:
                logger.error("All retries failed during triage: %s", e)
                return _local_clarification_check(extracted_fields, {
                    "classification": "Moderate",
                    "reasoning": f"Defaulted to Moderate due to network failure: {e}",
                    "needs_clarification": False,
                    "clarification_questions": [],
                })
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error during triage: %s", e)
            return _local_clarification_check(extracted_fields, {
                "classification": "Moderate",
                "reasoning": f"Defaulted to Moderate due to HTTP error: {e.response.status_code}",
                "needs_clarification": False,
                "clarification_questions": [],
            })
        except Exception as e:
            logger.error("Unexpected error during triage: %s", e)
            return _local_clarification_check(extracted_fields, {
                "classification": "Moderate",
                "reasoning": f"Defaulted to Moderate due to unexpected error: {e}",
                "needs_clarification": False,
                "clarification_questions": [],
            })

    try:
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        result = json.loads(raw_text)

        valid_classes = {"Simple", "Moderate", "Complex"}
        if result.get("classification") not in valid_classes:
            result["classification"] = "Moderate"
        result.setdefault("reasoning", "Classification determined by triage model.")
        result.setdefault("needs_clarification", False)
        result.setdefault("clarification_questions", [])

        # Cap at 3 questions
        result["clarification_questions"] = result["clarification_questions"][:3]

        return result

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning("Failed to parse triage JSON: %s", e)
        return _local_clarification_check(extracted_fields, {
            "classification": "Moderate",
            "reasoning": "Triage defaulted to Moderate due to JSON parsing failure.",
            "needs_clarification": False,
            "clarification_questions": [],
        })
    except Exception as e:
        logger.error("Unexpected error during triage parse: %s", e)
        return _local_clarification_check(extracted_fields, {
            "classification": "Moderate",
            "reasoning": f"Defaulted to Moderate: {e}",
            "needs_clarification": False,
            "clarification_questions": [],
        })


def _local_clarification_check(extracted_fields: dict, base_result: dict) -> dict:
    """
    Local rule-based clarification check — runs even without Gemini API.
    Flags missing critical fields that would materially change the recommendation.
    """
    questions = list(base_result.get("clarification_questions", []))
    industry = extracted_fields.get("industry", "unknown").lower()
    data_sens = extracted_fields.get("data_sensitivity", "none").lower()
    daily_req = extracted_fields.get("daily_requests", "unknown")
    budget = extracted_fields.get("monthly_budget_usd")
    budget_hint = extracted_fields.get("budget_hint", "unknown")
    compliance_region = extracted_fields.get("compliance_region", "unknown").lower()
    task_type = extracted_fields.get("task_type", "unknown").lower()
    avg_input = extracted_fields.get("avg_input_tokens", "unknown")

    # Rule 1: daily_requests unknown
    if daily_req == "unknown" and len(questions) < 3:
        questions.append(
            "How many requests per day do you expect?\n"
            "Options: Under 1,000 / 1,000–10,000 / 10,000–100,000 / Over 100,000"
        )

    # Rule 2: no budget info
    if budget is None and budget_hint == "unknown" and len(questions) < 3:
        questions.append(
            "What is your approximate monthly budget for AI infrastructure (in USD)?\n"
            "Options: Under $100 / $100–$500 / $500–$2,000 / $2,000–$10,000 / No limit"
        )

    # Rule 3: missing compliance region for sensitive data
    if (compliance_region == "unknown"
            and data_sens in ("medium", "high", "critical")
            and len(questions) < 3):
        questions.append(
            "Which country or region will your users be in?\n"
            "Options: EU / USA / India / UK / Australia / Canada / Global"
        )

    # Rule 4: industry implies sensitivity mismatch
    if (industry in ("healthcare", "finance", "legal")
            and data_sens in ("none", "low")
            and len(questions) < 3):
        questions.append(
            "Will your system process patient records, financial data, or legal documents?\n"
            "Options: No personal data / Names and emails only / Financial records / Health records"
        )

    # Rule 5: document task but unknown token size
    if (task_type in ("document_processing", "summarization", "extraction", "search")
            and avg_input == "unknown"
            and len(questions) < 3):
        questions.append(
            "How long are the documents or inputs you will process?\n"
            "Options: Short (<200 words) / Medium (1–5 pages) / Long (5–20 pages) / Very long (20+ pages)"
        )

    result = dict(base_result)
    if questions:
        result["needs_clarification"] = True
        result["clarification_questions"] = questions[:3]
    else:
        result["needs_clarification"] = False
        result["clarification_questions"] = []

    return result
