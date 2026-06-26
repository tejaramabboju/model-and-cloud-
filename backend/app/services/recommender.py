"""
Recommender service — generates the complete 8-section guidebook recommendation.
Uses Google Gemini for full LLM-based generation, falls back to a comprehensive
rule-based engine that also generates all 8 sections locally.
"""

import asyncio
import json
import logging
import re
import httpx

from app.config import get_settings
from app.services.compliance import check_compliance
from app.services.knowledge_base import get_all_models, get_all_cloud_providers

logger = logging.getLogger(__name__)

RECOMMENDATION_SYSTEM_PROMPT = """
You are an expert AI infrastructure advisor and solution architect.
Your output is a complete, actionable guidebook — not just a model name.

You receive:
  - The user's use case description and extracted requirements
  - A complexity classification (Simple | Moderate | Complex)
  - A knowledge base of available models, cloud providers, and compliance data
  - The user's budget, token estimates, daily volume, and cloud preferences

YOUR JOB: Generate a comprehensive structured recommendation with 8 sections.

CRITICAL RULES:
1. NEVER always recommend Claude. Score ALL models objectively based on cost, fit, and benchmarks.
2. If user has a budget, ONLY recommend models whose monthly cost fits within it.
3. Use the exact pricing from the knowledge base.
4. For EU/GDPR compliance, prefer Mistral (France-based) or EU cloud regions.
5. For healthcare/HIPAA, prefer AWS or Azure with certified regions.
6. For cost-sensitive use cases, prefer Gemini Flash, DeepSeek Flash, or Amazon Nova Micro.

Return ONLY a single valid JSON object with ALL of these top-level keys:

{
  "recommended_model": "Model Name",
  "model_provider": "Provider Name",
  "model_rationale": "3-5 sentence explanation of why this model fits",
  "model_strengths": ["strength 1 specific to this use case", "strength 2", "strength 3"],
  "model_limitations": ["limitation 1", "limitation 2"],

  "recommended_cloud": "AWS|GCP|Azure",
  "recommended_region": "region-id (Location, Country)",
  "cloud_rationale": "2-3 sentences why this cloud and region",
  "cloud_services": [
    {
      "service_name": "AWS Bedrock",
      "purpose": "Managed LLM API access",
      "why_needed": "Provides secure, scalable access to Claude models without managing infrastructure",
      "setup_complexity": "Easy"
    },
    {
      "service_name": "Amazon S3",
      "purpose": "Document and data storage",
      "why_needed": "Store user-uploaded documents, prompt templates, and output logs",
      "setup_complexity": "Easy"
    },
    {
      "service_name": "AWS Lambda",
      "purpose": "Serverless compute",
      "why_needed": "Handle API requests without managing servers, scales automatically",
      "setup_complexity": "Medium"
    },
    {
      "service_name": "API Gateway",
      "purpose": "API routing and rate limiting",
      "why_needed": "Expose your LLM backend to clients with auth and throttling",
      "setup_complexity": "Medium"
    },
    {
      "service_name": "AWS IAM",
      "purpose": "Access control",
      "why_needed": "Manage permissions for Bedrock, S3, and other services securely",
      "setup_complexity": "Easy"
    },
    {
      "service_name": "CloudWatch",
      "purpose": "Monitoring and logging",
      "why_needed": "Track token usage, latency, errors, and set cost alerts",
      "setup_complexity": "Easy"
    }
  ],

  "cost_breakdown": {
    "llm_cost_monthly": 45.60,
    "llm_cost_per_1k_requests": 0.152,
    "llm_cost_per_user": null,
    "cloud_infra_cost_monthly": 25.00,
    "total_estimated_monthly": 70.60,
    "baseline_comparison": 450.00,
    "estimated_savings": 379.40,
    "assumptions": ["Assumed 10,000 requests/day", "Assumed 500 input + 300 output tokens per request"],
    "cost_breakdown_items": [
      {"item": "AWS Bedrock (LLM calls)", "monthly_usd": 45.60},
      {"item": "S3 storage (10GB)", "monthly_usd": 0.23},
      {"item": "Lambda invocations", "monthly_usd": 2.00},
      {"item": "API Gateway (1M calls)", "monthly_usd": 3.50},
      {"item": "CloudWatch logs", "monthly_usd": 1.00}
    ]
  },
  "within_budget": true,

  "development_guide": [
    {
      "phase": 1,
      "phase_name": "Cloud Account Setup",
      "duration": "1 day",
      "steps": [
        {
          "step": "Create an AWS account",
          "detail": "Sign up at aws.amazon.com and enable billing alerts to avoid surprises.",
          "resources": ["https://aws.amazon.com/free/"]
        },
        {
          "step": "Enable AWS Bedrock access",
          "detail": "Request model access in the Bedrock console for the models you need.",
          "resources": ["https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html"]
        }
      ]
    },
    {
      "phase": 2,
      "phase_name": "Backend API Setup",
      "duration": "2-3 days",
      "steps": [
        {
          "step": "Create a FastAPI backend",
          "detail": "Use Python FastAPI to build the LLM API endpoint. Install boto3 for Bedrock access.",
          "resources": ["https://fastapi.tiangolo.com", "https://boto3.amazonaws.com/v1/documentation/api/latest/"]
        }
      ]
    },
    {
      "phase": 3,
      "phase_name": "Deploy & Monitor",
      "duration": "1-2 days",
      "steps": [
        {
          "step": "Deploy to AWS Lambda",
          "detail": "Package your FastAPI app with Mangum adapter and deploy to Lambda behind API Gateway.",
          "resources": ["https://mangum.io"]
        }
      ]
    }
  ],

  "architecture_summary": "2-3 paragraphs describing the overall system architecture in plain English.",
  "architecture_components": ["API Gateway", "Lambda", "Bedrock", "S3", "CloudWatch", "IAM"],
  "data_flow": [
    "1. User sends request to API Gateway endpoint",
    "2. API Gateway triggers Lambda function",
    "3. Lambda retrieves context from S3 if needed",
    "4. Lambda calls AWS Bedrock with the prompt",
    "5. Bedrock returns response from the LLM",
    "6. Lambda returns response to user via API Gateway",
    "7. CloudWatch logs usage and latency metrics"
  ],

  "compliance_flags": [
    {"flag": "Data residency", "status": "pass", "detail": "US-East-1 region keeps data within USA", "note": ""},
    {"flag": "SOC2 compliance", "status": "pass", "detail": "AWS us-east-1 is SOC2 certified", "note": ""}
  ],
  "security_recommendations": [
    "Enable VPC endpoint for Bedrock to avoid traffic over public internet",
    "Use AWS Secrets Manager for API keys, never hardcode in Lambda",
    "Enable CloudTrail for audit logging of all Bedrock API calls",
    "Set IAM least-privilege roles — Lambda should only access what it needs"
  ],

  "alternatives": [
    {
      "model": "Alternative Model Name",
      "cloud": "AWS",
      "region": "us-east-1 (N. Virginia, USA)",
      "estimated_monthly_cost": 120.00,
      "trade_off": "Higher cost but better reasoning capability for complex tasks",
      "best_for": "Use cases requiring advanced multi-step reasoning"
    }
  ],

  "confidence_score": 82,
  "confidence_reasoning": "High confidence because the use case is well-defined with clear task type, compliance region, and scale.",
  "missing_info_impact": "Daily request volume was unknown — assumed 10,000/day. Actual cost may vary."
}

Tailor cloud_services to the chosen cloud (AWS/GCP/Azure) — use the right service names.
Tailor development_guide to the user's team_expertise (beginner gets more detail, expert gets less).
Provide 2-3 alternatives with different models and/or clouds.
"""


# ─── Main entry point ──────────────────────────────────────────────────────────

async def generate_recommendation(
    description: str,
    extracted_fields: dict,
    triage: dict,
    kb_context: str,
    compliant_options: list[dict],
    forced_model: str | None = None,
    forced_cloud: str | None = None,
) -> dict:
    """
    Generate the full 8-section guidebook recommendation using Gemini.
    Falls back to a comprehensive rule-based engine if API unavailable.
    """
    settings = get_settings()
    api_key = settings.GEMINI_API_KEY

    if not api_key or "gemini-key" in api_key or "your-key" in api_key:
        logger.warning("Gemini API key not configured. Using rule-based guidebook generator.")
        return _smart_fallback_recommendation(
            extracted_fields, triage, compliant_options, description,
            forced_model=forced_model, forced_cloud=forced_cloud
        )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    user_content = _build_user_content(
        description, extracted_fields, triage, kb_context, compliant_options,
        forced_model=forced_model, forced_cloud=forced_cloud
    )

    payload = {
        "contents": [{"parts": [{"text": user_content}]}],
        "systemInstruction": {"parts": [{"text": RECOMMENDATION_SYSTEM_PROMPT}]},
        "generationConfig": {"responseMimeType": "application/json"},
    }

    max_retries = 3
    retry_delay = 1.0
    response = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                if response.status_code == 200:
                    break
                elif response.status_code in (429, 503) and attempt < max_retries - 1:
                    logger.warning("Gemini API %s for recommendation. Retry in %ss...", response.status_code, retry_delay)
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2.0
                else:
                    response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            if attempt < max_retries - 1:
                logger.warning("Network error during recommendation: %s. Retry...", e)
                await asyncio.sleep(retry_delay)
                retry_delay *= 2.0
            else:
                logger.error("All retries failed. Using rule-based fallback.")
                return _smart_fallback_recommendation(
                    extracted_fields, triage, compliant_options, description,
                    forced_model=forced_model, forced_cloud=forced_cloud
                )
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error during recommendation: %s", e)
            return _smart_fallback_recommendation(
                extracted_fields, triage, compliant_options, description,
                forced_model=forced_model, forced_cloud=forced_cloud
            )
        except Exception as e:
            logger.error("Unexpected error during recommendation: %s", e)
            return _smart_fallback_recommendation(
                extracted_fields, triage, compliant_options, description,
                forced_model=forced_model, forced_cloud=forced_cloud
            )

    try:
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        recommendation = json.loads(raw_text)
        recommendation = _validate_and_fill(
            recommendation, extracted_fields, triage, compliant_options,
            forced_model=forced_model, forced_cloud=forced_cloud
        )
        return recommendation

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning("Failed to parse Gemini recommendation JSON: %s. Using fallback.", e)
        return _smart_fallback_recommendation(
            extracted_fields, triage, compliant_options, description,
            forced_model=forced_model, forced_cloud=forced_cloud
        )
    except Exception as e:
        logger.error("Unexpected error parsing recommendation: %s", e)
        return _smart_fallback_recommendation(
            extracted_fields, triage, compliant_options, description,
            forced_model=forced_model, forced_cloud=forced_cloud
        )


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _build_user_content(description, extracted_fields, triage, kb_context, compliant_options, forced_model=None, forced_cloud=None):
    compliant_summary = "\n".join(
        f"- {o.get('model')} on {o.get('cloud')}, region: {o.get('region',{}).get('id','?')} ({o.get('region',{}).get('location','?')})"
        for o in compliant_options[:8]
    ) or "No specific compliant options — use general knowledge base."

    content = (
        f"Use case description:\n{description}\n\n"
        f"Extracted requirements:\n{json.dumps(extracted_fields, indent=2)}\n\n"
        f"Complexity: {triage.get('classification', 'Moderate')} — {triage.get('reasoning', '')}\n\n"
        f"{kb_context}\n\n"
        f"Compliant deployment options:\n{compliant_summary}\n\n"
    )

    if forced_model or forced_cloud:
        content += "### FORCED CHOICE INSTRUCTION (CRITICAL)\n"
        if forced_model:
            content += f"- You MUST select '{forced_model}' as the primary recommended model. Set the 'recommended_model' field to exactly '{forced_model}'.\n"
        if forced_cloud:
            content += f"- You MUST select '{forced_cloud}' as the primary recommended cloud provider. Set the 'recommended_cloud' field to exactly '{forced_cloud}'.\n"
        content += "You MUST align all other guidebook sections (costs, cloud services, architecture, dev guide, compliance flags, alternatives) with this forced choice. Do not choose another model/cloud.\n\n"

    content += "Generate the complete 8-section guidebook recommendation."
    return content


def _validate_and_fill(
    rec: dict,
    extracted_fields: dict,
    triage: dict,
    compliant_options: list,
    forced_model: str | None = None,
    forced_cloud: str | None = None,
) -> dict:
    """Ensure all required keys exist with sane defaults."""
    defaults = {
        "recommended_model": "Gemini 2.5 Flash",
        "model_provider": "Google",
        "model_rationale": "Selected based on cost efficiency and task fit.",
        "model_strengths": [],
        "model_limitations": [],
        "recommended_cloud": "GCP",
        "recommended_region": "us-central1 (Iowa, USA)",
        "region": "us-central1 (Iowa, USA)",
        "cloud_rationale": "GCP offers native Vertex AI integration.",
        "cloud_services": [],
        "cost_breakdown": None,
        "within_budget": None,
        "development_guide": [],
        "architecture_summary": "",
        "architecture_components": [],
        "data_flow": [],
        "compliance_flags": [],
        "security_recommendations": [],
        "alternatives": [],
        "confidence_score": 70,
        "confidence_reasoning": "",
        "missing_info_impact": "none",
        "rationale": "",
        "estimated_monthly_cost": 0.0,
        "baseline_cost": 0.0,
    }

    for k, v in defaults.items():
        if k not in rec:
            rec[k] = v

    if forced_model or forced_cloud:
        rec_model = rec.get("recommended_model", "")
        rec_cloud = rec.get("recommended_cloud", "")

        model_changed = forced_model and forced_model.lower() != rec_model.lower()
        cloud_changed = forced_cloud and forced_cloud.lower() != rec_cloud.lower()

        if model_changed or cloud_changed:
            logger.info("Forced choice mismatch. Correcting LLM response in validator.")
            if forced_model:
                rec["recommended_model"] = forced_model
            if forced_cloud:
                rec["recommended_cloud"] = forced_cloud

            all_models = get_all_models()
            target_model = None
            for m in all_models:
                if forced_model and (m["name"].lower() == forced_model.lower() or forced_model.lower() in m["name"].lower()):
                    target_model = m
                    break
            if not target_model:
                for m in all_models:
                    if m["name"].lower() == rec_model.lower():
                        target_model = m
                        break
            if not target_model:
                target_model = all_models[0]

            rec["model_provider"] = target_model.get("provider", "")

            final_cloud = forced_cloud or rec_cloud
            compliance_region = extracted_fields.get("compliance_region", "").lower()
            if "eu" in compliance_region or "europe" in compliance_region:
                region_map = {"AWS": "eu-west-1 (Ireland, EU)", "GCP": "europe-west1 (Belgium, EU)", "Azure": "westeurope (Netherlands, EU)"}
                final_region = region_map.get(final_cloud, "us-east-1 (N. Virginia, USA)")
            elif "india" in compliance_region:
                region_map = {"AWS": "ap-south-1 (Mumbai, India)", "GCP": "asia-south1 (Mumbai, India)", "Azure": "centralindia (Pune, India)"}
                final_region = region_map.get(final_cloud, "us-east-1 (N. Virginia, USA)")
            else:
                region_map = {"AWS": "us-east-1 (N. Virginia, USA)", "GCP": "us-central1 (Iowa, USA)", "Azure": "eastus (Virginia, USA)"}
                final_region = region_map.get(final_cloud, "us-east-1 (N. Virginia, USA)")

            rec["recommended_region"] = final_region
            rec["region"] = final_region

            cb, within_budget = _build_cost_breakdown(extracted_fields, triage, target_model, final_cloud)
            rec["cost_breakdown"] = cb
            rec["within_budget"] = within_budget
            rec["estimated_monthly_cost"] = cb["total_estimated_monthly"]
            rec["baseline_cost"] = cb["baseline_comparison"]

            rec["cloud_services"] = _build_cloud_services(
                final_cloud,
                extracted_fields.get("task_type", "unknown"),
                extracted_fields.get("data_sensitivity", "none"),
                triage.get("classification", "Moderate")
            )

            summary, components, flow = _build_architecture(
                final_cloud,
                extracted_fields.get("task_type", "unknown"),
                triage.get("classification", "Moderate")
            )
            rec["architecture_summary"] = summary
            rec["architecture_components"] = components
            rec["data_flow"] = flow

            flags, recs = _build_compliance_flags(extracted_fields, final_cloud, final_region)
            rec["compliance_flags"] = flags
            rec["security_recommendations"] = recs

    # Sync region aliases
    if not rec.get("region"):
        rec["region"] = rec.get("recommended_region", "")
    if not rec.get("recommended_region"):
        rec["recommended_region"] = rec.get("region", "")

    # Legacy rationale
    if not rec.get("rationale"):
        rec["rationale"] = rec.get("model_rationale", "")

    # Sync estimated_monthly_cost from cost_breakdown
    if rec.get("cost_breakdown") and isinstance(rec["cost_breakdown"], dict):
        cb = rec["cost_breakdown"]
        rec["estimated_monthly_cost"] = float(cb.get("total_estimated_monthly", 0))
        rec["baseline_cost"] = float(cb.get("baseline_comparison", 0))
        if not rec.get("rationale"):
            rec["rationale"] = rec.get("model_rationale", "")

    try:
        rec["confidence_score"] = max(0, min(100, int(rec["confidence_score"])))
    except (ValueError, TypeError):
        rec["confidence_score"] = 70

    return rec


# ─── Rule-based scoring engine ─────────────────────────────────────────────────

def _parse_budget(extracted_fields: dict) -> float | None:
    budget = extracted_fields.get("monthly_budget_usd")
    if budget is not None:
        try:
            return float(budget)
        except (ValueError, TypeError):
            pass
    budget_hint = str(extracted_fields.get("budget_hint", "")).lower()
    if not budget_hint or budget_hint == "unknown":
        return None
    matches = re.findall(r"\$?([\d,]+\.?\d*)", budget_hint)
    if matches:
        try:
            val = float(matches[0].replace(",", ""))
            if val < 1:
                val = val * 10_000 * 30
            return val
        except ValueError:
            pass
    if any(w in budget_hint for w in ["low", "tight", "minimal", "cheap"]):
        return 200.0
    if any(w in budget_hint for w in ["medium", "moderate", "mid"]):
        return 2000.0
    if any(w in budget_hint for w in ["high", "enterprise", "unlimited"]):
        return 50000.0
    return None


def _resolve_volume(extracted_fields: dict, triage: dict) -> tuple[int, int, int]:
    """Resolve daily_requests, avg_input_tokens, avg_output_tokens to ints."""
    classification = triage.get("classification", "Moderate")

    dr_raw = str(extracted_fields.get("daily_requests", "unknown"))
    in_raw = str(extracted_fields.get("avg_input_tokens", "unknown"))
    out_raw = str(extracted_fields.get("avg_output_tokens", "unknown"))

    if classification == "Simple":
        default_dr, default_in, default_out = 1_000, 200, 100
    elif classification == "Complex":
        default_dr, default_in, default_out = 5_000, 1000, 500
    else:
        default_dr, default_in, default_out = 10_000, 500, 300

    try:
        daily_req = int(dr_raw.replace(",", "")) if dr_raw != "unknown" else default_dr
    except ValueError:
        daily_req = default_dr

    try:
        avg_in = int(in_raw.replace(",", "")) if in_raw != "unknown" else default_in
    except ValueError:
        avg_in = default_in

    try:
        avg_out = int(out_raw.replace(",", "")) if out_raw != "unknown" else default_out
    except ValueError:
        avg_out = default_out

    return daily_req, avg_in, avg_out


def _score_model(model: dict, extracted_fields: dict, triage: dict, budget_limit: float | None, description_lower: str) -> tuple[float, float]:
    score = 50.0
    classification = triage.get("classification", "Moderate")
    scale = extracted_fields.get("scale_volume", "medium").lower()
    data_sensitivity = extracted_fields.get("data_sensitivity", "low").lower()
    compliance_region = extracted_fields.get("compliance_region", "").lower()
    latency_need = extracted_fields.get("latency_requirement", extracted_fields.get("latency_need", "unknown")).lower()
    task_type = extracted_fields.get("task_type", "").lower()
    existing_cloud = extracted_fields.get("existing_cloud", "none").lower()

    daily_req, avg_in, avg_out = _resolve_volume(extracted_fields, triage)

    in_cost = model["cost_per_1k_input_tokens"] * (avg_in / 1000) * daily_req * 30
    out_cost = model["cost_per_1k_output_tokens"] * (avg_out / 1000) * daily_req * 30
    monthly_cost = round(in_cost + out_cost, 2)

    # Hard budget disqualification
    if budget_limit is not None and monthly_cost > budget_limit * 1.1:
        return -1000.0, monthly_cost

    # Cost score
    cost_ratio = monthly_cost / 5000.0
    score += max(-25, 25 - (cost_ratio * 50))

    # Complexity fit
    tier = model.get("tier", "Medium")
    if classification == "Simple":
        score += 20 if tier == "Small" else (5 if tier == "Medium" else -15)
    elif classification == "Complex":
        score += 20 if tier == "Large" else (5 if tier == "Medium" else -20)
    else:
        score += 15 if tier == "Medium" else (8 if tier == "Large" else 5)

    # Latency
    if any(w in latency_need for w in ["realtime", "fast", "<1", "100ms"]):
        if tier == "Small":
            score += 10
        elif tier == "Large":
            score -= 5

    # Existing cloud preference
    provider = model.get("provider", "").lower()
    if existing_cloud != "none" and existing_cloud != "unknown":
        cloud_model_map = {
            "aws": ["amazon", "anthropic", "meta", "mistral"],
            "gcp": ["google", "anthropic", "meta"],
            "azure": ["microsoft", "openai", "meta", "mistral"],
        }
        preferred_providers = cloud_model_map.get(existing_cloud, [])
        if any(p in provider for p in preferred_providers):
            score += 8

    # Workload cloud suitability boosts
    # 1. GCP: Containerized SaaS/AI/ML tasks
    is_gcp_workload = (
        any(w in description_lower for w in ["saas", "container", "docker", "kubernetes", "gke", "ml", "machine learning", "ai", "predictive", "nlp", "extract", "chatbot", "stream", "vertex"]) or
        any(w in task_type for w in ["ai", "ml", "data", "analytics", "container", "saas", "extraction", "chatbot"])
    )
    if is_gcp_workload:
        if any(p in provider for p in ["google", "anthropic", "meta"]):
            score += 10
            
    # 2. Azure: Microsoft/Hybrid systems
    is_azure_workload = (
        any(w in description_lower for w in ["microsoft", "windows", "hybrid", "active directory", "on-premise", "on-prem", "sql server", "dotnet", "c#", "azure arc", "ad", "office"]) or
        extracted_fields.get("on_premise_required") is True
    )
    if is_azure_workload:
        if any(p in provider for p in ["microsoft", "openai", "meta", "mistral"]):
            score += 10
            
    # 3. AWS: Massive scale networking
    scale = str(extracted_fields.get("scale_volume", "medium")).lower()
    daily_requests = str(extracted_fields.get("daily_requests", "unknown")).lower()
    is_aws_workload = (
        any(w in description_lower for w in ["massive", "global", "high availability", "scale", "volume", "networking", "custom routing", "vpc", "million", "tb", "petabyte", "cdn", "cloudfront", "aws"]) or
        scale in ("high", "massive") or "100,000" in daily_requests or "100k" in daily_requests
    )
    if is_aws_workload:
        if any(p in provider for p in ["amazon", "anthropic", "meta", "mistral"]):
            score += 10

    # Data sensitivity / privacy
    if data_sensitivity in ("high", "critical"):
        if "meta" in provider or "self-hosted" in provider:
            score += 15
    if "eu" in compliance_region or "gdpr" in description_lower:
        if "mistral" in provider:
            score += 12

    # Task keyword match
    best_for_text = " ".join(model.get("best_for", [])).lower()
    for kw in ["chat", "classification", "extraction", "reasoning", "coding",
                "summarization", "rag", "multilingual", "agent", "routing",
                "multimodal", "document", "analysis"]:
        if kw in task_type or kw in description_lower:
            if kw in best_for_text:
                score += 5

    # Benchmark scores
    gpqa = model.get("benchmark_gpqa")
    swe = model.get("benchmark_swe")
    tps = model.get("speed_tps")
    if gpqa:
        score += 10 if gpqa >= 90 else (6 if gpqa >= 80 else (3 if gpqa >= 70 else 0))
    if swe and any(w in description_lower for w in ["cod", "software", "debug", "develop"]):
        score += 10 if swe >= 80 else (5 if swe >= 60 else 0)
    if tps and any(w in latency_need for w in ["realtime", "fast", "instant"]):
        score += 12 if tps >= 500 else (7 if tps >= 200 else (3 if tps >= 100 else 0))

    # Context window
    ctx_match = re.search(r"(\d[\d,]*)\s*(?:k)?\s*(?:context|window)", description_lower)
    if ctx_match:
        try:
            needed = int(ctx_match.group(1).replace(",", ""))
            if "k" in ctx_match.group(0).lower():
                needed *= 1000
            score += 8 if model.get("max_context", 0) >= needed else -20
        except ValueError:
            pass

    # Nova/Amazon bonus
    if "nova" in model.get("name", "").lower() and "amazon" in provider:
        if "aws" in description_lower or "amazon" in description_lower or "nova" in description_lower:
            score += 15

    return score, monthly_cost


def _pick_cloud_for_model(model: dict, extracted_fields: dict, compliant_options: list) -> tuple[str, str]:
    provider = model.get("provider", "").lower()
    compliance_region = extracted_fields.get("compliance_region", "").lower()
    existing_cloud = extracted_fields.get("existing_cloud", "none").lower()
    description_lower = str(extracted_fields.get("description", "")).lower() or ""
    task_type = str(extracted_fields.get("task_type", "")).lower()

    # Score each cloud option
    cloud_scores = {"AWS": 0, "Azure": 0, "GCP": 0}
    
    # GCP: Containerized SaaS/AI/ML tasks
    is_gcp_workload = (
        any(w in description_lower for w in ["saas", "container", "docker", "kubernetes", "gke", "ml", "machine learning", "ai", "predictive", "nlp", "extract", "chatbot", "stream", "vertex"]) or
        any(w in task_type for w in ["ai", "ml", "data", "analytics", "container", "saas", "extraction", "chatbot"])
    )
    if is_gcp_workload:
        cloud_scores["GCP"] += 15
        
    # Azure: Microsoft/Hybrid systems
    is_azure_workload = (
        any(w in description_lower for w in ["microsoft", "windows", "hybrid", "active directory", "on-premise", "on-prem", "sql server", "dotnet", "c#", "azure arc", "ad", "office"]) or
        extracted_fields.get("on_premise_required") is True
    )
    if is_azure_workload:
        cloud_scores["Azure"] += 15
        
    # AWS: Massive scale networking
    scale = str(extracted_fields.get("scale_volume", "medium")).lower()
    daily_requests = str(extracted_fields.get("daily_requests", "unknown")).lower()
    is_aws_workload = (
        any(w in description_lower for w in ["massive", "global", "high availability", "scale", "volume", "networking", "custom routing", "vpc", "million", "tb", "petabyte", "cdn", "cloudfront", "aws"]) or
        scale in ("high", "massive") or "100,000" in daily_requests or "100k" in daily_requests
    )
    if is_aws_workload:
        cloud_scores["AWS"] += 15

    # Determine supported clouds for this model
    supported_clouds = []
    model_name_lower = model["name"].lower()
    aws_models = [
        "claude haiku 4.5", "claude sonnet 4.6", "claude 3.5 sonnet", "claude 3.5 haiku",
        "amazon nova micro", "amazon nova lite", "amazon nova pro",
        "llama 3.1 70b", "llama 3.3 70b", "mistral large", "command r+"
    ]
    azure_models = [
        "gpt-4o mini", "gpt-4o", "openai o1", "openai o3-mini", "phi-4",
        "llama 3.1 70b", "llama 3.3 70b", "mistral large", "deepseek-r1", "deepseek-v3"
    ]
    gcp_models = [
        "gemini 1.5 flash", "gemini 1.5 pro", "gemini 2.5 flash", "gemini 2.5 pro",
        "claude haiku 4.5", "claude sonnet 4.6", "llama 3.1 70b", "llama 3.3 70b",
        "gemma 2 27b", "qwen 2.5 72b", "deepseek-r1", "deepseek-v3"
    ]
    
    if any(m in model_name_lower for m in aws_models) or "nova" in model_name_lower:
        supported_clouds.append("AWS")
    if any(m in model_name_lower for m in azure_models) or "gpt-4" in model_name_lower or "openai" in model_name_lower:
        supported_clouds.append("Azure")
    if any(m in model_name_lower for m in gcp_models) or "gemini" in model_name_lower or "gemma" in model_name_lower:
        supported_clouds.append("GCP")

    # Prefer existing cloud if possible, but score if multiple compliant options exist
    matching_opts = [opt for opt in compliant_options if opt.get("model", "").lower() == model["name"].lower()]
    if matching_opts:
        def get_opt_score(opt):
            c = opt.get("cloud", "AWS").upper()
            base_score = cloud_scores.get(c, 0)
            if existing_cloud == c.lower():
                base_score += 30
            return base_score
        
        best_opt = max(matching_opts, key=get_opt_score)
        r = best_opt.get("region", {})
        return best_opt.get("cloud", "AWS"), f"{r.get('id', 'us-east-1')} ({r.get('location', 'N. Virginia, USA')})"

    # Fallback to selecting best supported cloud
    if not supported_clouds:
        if "amazon" in provider or "nova" in model_name_lower:
            supported_clouds = ["AWS"]
        elif "google" in provider or "gemini" in model_name_lower or "gemma" in model_name_lower:
            supported_clouds = ["GCP"]
        elif "openai" in provider or "microsoft" in provider:
            supported_clouds = ["Azure"]
        elif "anthropic" in provider or "claude" in model_name_lower:
            supported_clouds = ["AWS", "GCP"]
        else:
            supported_clouds = ["AWS", "GCP", "Azure"]

    def get_cloud_default_priority(c):
        c = c.upper()
        score = cloud_scores.get(c, 0)
        if existing_cloud == c.lower():
            score += 30
        if c == "AWS" and ("amazon" in provider or "claude" in model_name_lower or "nova" in model_name_lower):
            score += 5
        elif c == "GCP" and ("google" in provider or "gemini" in model_name_lower or "gemma" in model_name_lower):
            score += 5
        elif c == "Azure" and ("openai" in provider or "microsoft" in provider or "gpt" in model_name_lower):
            score += 5
        return score

    cloud = max(supported_clouds, key=get_cloud_default_priority)

    if "eu" in compliance_region or "europe" in compliance_region:
        region_map = {"AWS": "eu-west-1 (Ireland, EU)", "GCP": "europe-west1 (Belgium, EU)", "Azure": "westeurope (Netherlands, EU)"}
    elif "india" in compliance_region:
        region_map = {"AWS": "ap-south-1 (Mumbai, India)", "GCP": "asia-south1 (Mumbai, India)", "Azure": "centralindia (Pune, India)"}
    else:
        region_map = {"AWS": "us-east-1 (N. Virginia, USA)", "GCP": "us-central1 (Iowa, USA)", "Azure": "eastus (Virginia, USA)"}

    return cloud, region_map.get(cloud, "us-east-1 (N. Virginia, USA)")


def _build_cloud_services(cloud: str, task_type: str, data_sensitivity: str, classification: str) -> list[dict]:
    """Generate a relevant cloud services list for the chosen cloud."""
    task_type = task_type.lower()
    services = []

    if cloud == "AWS":
        services = [
            {"service_name": "AWS Bedrock", "purpose": "Managed LLM API access", "why_needed": "Deploy and call the recommended LLM securely without managing model infrastructure.", "setup_complexity": "Easy"},
            {"service_name": "AWS Lambda", "purpose": "Serverless compute", "why_needed": "Handle API requests and LLM calls automatically — scales to zero when idle.", "setup_complexity": "Medium"},
            {"service_name": "API Gateway", "purpose": "API routing and rate limiting", "why_needed": "Expose your LLM backend as a secure REST API with built-in throttling and auth.", "setup_complexity": "Medium"},
            {"service_name": "Amazon S3", "purpose": "Storage for documents and logs", "why_needed": "Store uploaded files, prompt templates, conversation logs, and outputs.", "setup_complexity": "Easy"},
            {"service_name": "AWS IAM", "purpose": "Access control and permissions", "why_needed": "Grant least-privilege access between services — required for Bedrock security.", "setup_complexity": "Easy"},
            {"service_name": "Amazon CloudWatch", "purpose": "Monitoring and alerting", "why_needed": "Track token usage, latency, error rates, and set cost budget alerts.", "setup_complexity": "Easy"},
        ]
        if data_sensitivity in ("high", "critical"):
            services.append({"service_name": "AWS KMS", "purpose": "Encryption key management", "why_needed": "Encrypt data at rest in S3 and DynamoDB with customer-managed keys.", "setup_complexity": "Medium"})
            services.append({"service_name": "AWS Secrets Manager", "purpose": "Secure secrets storage", "why_needed": "Store API keys and credentials securely — never hardcode in Lambda.", "setup_complexity": "Easy"})
        if task_type in ("chat", "recommendation", "search"):
            services.append({"service_name": "Amazon DynamoDB", "purpose": "Conversation history and session storage", "why_needed": "Low-latency NoSQL store for chat sessions and user context.", "setup_complexity": "Easy"})
    elif cloud == "GCP":
        services = [
            {"service_name": "Vertex AI", "purpose": "Managed LLM hosting and inference", "why_needed": "Native Gemini and Claude model access with enterprise-grade SLA.", "setup_complexity": "Easy"},
            {"service_name": "Cloud Run", "purpose": "Serverless container compute", "why_needed": "Deploy your API backend in a container that auto-scales to demand.", "setup_complexity": "Medium"},
            {"service_name": "Cloud Storage", "purpose": "Object storage for documents", "why_needed": "Store uploaded documents, processed outputs, and prompt libraries.", "setup_complexity": "Easy"},
            {"service_name": "Cloud Endpoints / API Gateway", "purpose": "API management", "why_needed": "Manage API keys, rate limits, and traffic for your LLM endpoint.", "setup_complexity": "Medium"},
            {"service_name": "Cloud IAM", "purpose": "Access control", "why_needed": "Grant services the minimum permissions needed to call Vertex AI and Storage.", "setup_complexity": "Easy"},
            {"service_name": "Cloud Monitoring", "purpose": "Observability and alerting", "why_needed": "Monitor Cloud Run latency, Vertex AI usage, and set billing alerts.", "setup_complexity": "Easy"},
        ]
        if task_type in ("chat", "recommendation"):
            services.append({"service_name": "Firestore", "purpose": "Real-time conversation storage", "why_needed": "Store and sync chat sessions in real time across client devices.", "setup_complexity": "Easy"})
        if task_type in ("document_processing", "summarization"):
            services.append({"service_name": "BigQuery", "purpose": "Analytics and bulk processing", "why_needed": "Run large-scale batch analysis on processed documents and LLM outputs.", "setup_complexity": "Medium"})
    else:  # Azure
        services = [
            {"service_name": "Azure OpenAI / AI Studio", "purpose": "Managed LLM inference", "why_needed": "Access GPT, Claude, and other frontier models through Microsoft's enterprise infrastructure.", "setup_complexity": "Easy"},
            {"service_name": "Azure App Service / Container Apps", "purpose": "Managed compute", "why_needed": "Deploy your API backend with auto-scaling without managing VMs.", "setup_complexity": "Medium"},
            {"service_name": "Azure Blob Storage", "purpose": "Document and file storage", "why_needed": "Store uploaded files, conversation logs, and LLM output artifacts.", "setup_complexity": "Easy"},
            {"service_name": "Azure API Management", "purpose": "API gateway and throttling", "why_needed": "Rate-limit, secure, and monitor your LLM API surface.", "setup_complexity": "Medium"},
            {"service_name": "Azure Active Directory", "purpose": "Identity and access management", "why_needed": "Enterprise SSO and role-based access control for your application.", "setup_complexity": "Medium"},
            {"service_name": "Azure Monitor", "purpose": "Monitoring and cost management", "why_needed": "Track usage, set budgets, and receive alerts on anomalous spend.", "setup_complexity": "Easy"},
        ]
        if data_sensitivity in ("high", "critical"):
            services.append({"service_name": "Azure Key Vault", "purpose": "Secrets and key management", "why_needed": "Store API credentials and encryption keys outside your application code.", "setup_complexity": "Easy"})

    return services


def _build_development_guide(cloud: str, task_type: str, team_expertise: str, classification: str) -> list[dict]:
    """Generate a phased development guide tailored to team expertise and cloud."""
    is_beginner = team_expertise in ("beginner", "unknown")
    is_expert = team_expertise == "expert"

    model_service = {"AWS": "AWS Bedrock", "GCP": "Vertex AI", "Azure": "Azure OpenAI"}.get(cloud, "AWS Bedrock")
    compute = {"AWS": "AWS Lambda", "GCP": "Cloud Run", "Azure": "Azure Container Apps"}.get(cloud, "Lambda")
    storage = {"AWS": "Amazon S3", "GCP": "Cloud Storage", "Azure": "Azure Blob Storage"}.get(cloud, "Amazon S3")
    monitoring = {"AWS": "CloudWatch", "GCP": "Cloud Monitoring", "Azure": "Azure Monitor"}.get(cloud, "CloudWatch")
    console_url = {"AWS": "https://console.aws.amazon.com/bedrock", "GCP": "https://console.cloud.google.com/vertex-ai", "Azure": "https://oai.azure.com/"}.get(cloud, "https://console.aws.amazon.com/bedrock")

    phases = [
        {
            "phase": 1,
            "phase_name": "Cloud Account Setup",
            "duration": "Half day" if not is_beginner else "1 day",
            "steps": [
                {
                    "step": f"Create a {cloud} account and enable billing",
                    "detail": f"Sign up at {cloud.lower()}.amazon.com / cloud.google.com / azure.microsoft.com and set a billing alert to avoid unexpected charges." if is_beginner else f"Create the {cloud} account and configure billing alerts.",
                    "resources": [f"https://{'aws.amazon.com/free' if cloud=='AWS' else 'cloud.google.com/free' if cloud=='GCP' else 'azure.microsoft.com/free'}"]
                },
                {
                    "step": f"Enable {model_service} access",
                    "detail": f"Navigate to {model_service} in the {cloud} console and request access to the recommended model. This may take a few minutes to propagate.",
                    "resources": [console_url]
                },
            ]
        },
        {
            "phase": 2,
            "phase_name": "LLM API Integration",
            "duration": "1-2 days",
            "steps": [
                {
                    "step": f"Install the {cloud} SDK",
                    "detail": f"Install boto3 (AWS), google-cloud-aiplatform (GCP), or openai (Azure) in your Python environment." if is_beginner else f"Add the {cloud} SDK to your project.",
                    "resources": [f"https://{'boto3.amazonaws.com' if cloud=='AWS' else 'googleapis.github.io/python-aiplatform' if cloud=='GCP' else 'github.com/openai/openai-python'}"]
                },
                {
                    "step": "Write a test call to the LLM",
                    "detail": "Send a simple prompt to verify your credentials and model access work end-to-end before building the full app.",
                    "resources": [console_url]
                },
            ]
        },
        {
            "phase": 3,
            "phase_name": "Backend API Development",
            "duration": "2-4 days",
            "steps": [
                {
                    "step": "Create a FastAPI or Flask backend",
                    "detail": "Build a REST API endpoint that accepts user input, calls the LLM, and returns the response. Use FastAPI for async support." if is_beginner else "Implement the LLM call handler with proper prompt engineering.",
                    "resources": ["https://fastapi.tiangolo.com", "https://www.uvicorn.org"]
                },
                {
                    "step": "Add prompt engineering and context management",
                    "detail": f"Design your system prompt for {task_type}. If the task needs conversation history, implement a sliding window context approach.",
                    "resources": ["https://platform.openai.com/docs/guides/prompt-engineering"]
                },
            ]
        },
        {
            "phase": 4,
            "phase_name": "Storage and Database",
            "duration": "1 day",
            "steps": [
                {
                    "step": f"Set up {storage}",
                    "detail": f"Create a bucket/container for storing documents, logs, and outputs. Enable versioning for important data.",
                    "resources": []
                },
            ]
        },
        {
            "phase": 5,
            "phase_name": "Security and Access Control",
            "duration": "1-2 days" if not is_expert else "Half day",
            "steps": [
                {
                    "step": f"Configure IAM roles and policies",
                    "detail": f"Create a service role that grants your compute only the minimum permissions needed: {model_service} read access, {storage} read/write. Never use root credentials.",
                    "resources": []
                },
                {
                    "step": "Store secrets in a secrets manager",
                    "detail": "Use AWS Secrets Manager / GCP Secret Manager / Azure Key Vault to store API keys. Never hardcode credentials in your codebase.",
                    "resources": []
                },
            ]
        },
        {
            "phase": 6,
            "phase_name": "Deployment",
            "duration": "1-2 days",
            "steps": [
                {
                    "step": f"Containerize and deploy to {compute}",
                    "detail": f"Package your FastAPI app in a Docker container and deploy to {compute}. This handles auto-scaling automatically.",
                    "resources": ["https://docker.com/get-started"]
                },
            ]
        },
        {
            "phase": 7,
            "phase_name": "Monitoring and Cost Controls",
            "duration": "Half day",
            "steps": [
                {
                    "step": f"Set up {monitoring} dashboards",
                    "detail": "Create dashboards tracking: LLM API call count, total tokens used, latency p95, and error rate. Set a budget alert at 80% of your monthly budget.",
                    "resources": []
                },
                {
                    "step": "Implement rate limiting and caching",
                    "detail": "Add Redis or DynamoDB caching for frequent identical queries. Rate-limit users to prevent runaway costs.",
                    "resources": []
                },
            ]
        },
    ]

    return phases


def _build_architecture(cloud: str, task_type: str, classification: str) -> tuple[str, list[str], list[str]]:
    """Generate architecture summary, components, and data flow."""
    service_map = {
        "AWS": ("AWS Bedrock", "Lambda", "API Gateway", "S3", "DynamoDB", "CloudWatch", "IAM", "VPC"),
        "GCP": ("Vertex AI", "Cloud Run", "Cloud Endpoints", "Cloud Storage", "Firestore", "Cloud Monitoring", "IAM", "VPC"),
        "Azure": ("Azure OpenAI", "Container Apps", "API Management", "Blob Storage", "Cosmos DB", "Azure Monitor", "AD", "VNet"),
    }
    llm_svc, compute, gateway, storage, db, monitoring, iam, network = service_map.get(cloud, service_map["AWS"])

    summary = (
        f"The architecture follows a serverless-first pattern on {cloud} to minimize operational overhead. "
        f"User requests flow through {gateway}, which routes them to {compute} functions that handle business logic and LLM calls. "
        f"The LLM inference is handled by {llm_svc}, which provides secure, managed access to the recommended model without you needing to host or scale the model yourself.\n\n"
        f"All conversation history and session data is stored in {db} for low-latency reads, while documents and output files are persisted in {storage}. "
        f"Access control is managed by {iam} with least-privilege roles — each service can only access what it absolutely needs. "
        f"The entire infrastructure operates within a private {network} to prevent unauthorized access.\n\n"
        f"{monitoring} provides real-time visibility into token usage, latency, and cost. "
        f"Setting a budget alert at 80% of your monthly limit ensures you're notified before overspending."
    )

    components = [gateway, compute, llm_svc, storage, db, monitoring, iam, network, "Load Balancer", "CDN (optional)"]

    data_flow = [
        f"1. User sends request to {gateway} endpoint over HTTPS",
        f"2. {gateway} validates API key and routes request to {compute}",
        f"3. {compute} retrieves relevant context from {db} (conversation history / user session)",
        f"4. {compute} constructs the prompt and calls {llm_svc} with the model",
        f"5. {llm_svc} returns the LLM response to {compute}",
        f"6. {compute} processes the response, stores in {db} if needed, saves logs to {storage}",
        f"7. {compute} returns the formatted response to {gateway}",
        f"8. {gateway} sends response to the client",
        f"9. {monitoring} records token usage, latency, and cost metrics",
    ]

    return summary, components, data_flow


def _build_cost_breakdown(extracted_fields: dict, triage: dict, best_model: dict, cloud: str) -> dict:
    """Build a detailed cost breakdown for the recommendation."""
    daily_req, avg_in, avg_out = _resolve_volume(extracted_fields, triage)

    in_cost = best_model["cost_per_1k_input_tokens"] * (avg_in / 1000) * daily_req * 30
    out_cost = best_model["cost_per_1k_output_tokens"] * (avg_out / 1000) * daily_req * 30
    llm_monthly = round(in_cost + out_cost, 2)
    cost_per_1k = round((llm_monthly / max(daily_req * 30, 1)) * 1000, 4)

    # Baseline using GPT-4o
    baseline = round(
        daily_req * avg_in / 1000 * 0.005 * 30 +
        daily_req * avg_out / 1000 * 0.015 * 30, 2
    )

    # Infra cost estimate
    cloud_infra = {"AWS": 28.50, "GCP": 22.00, "Azure": 31.00}.get(cloud, 28.50)

    total = round(llm_monthly + cloud_infra, 2)
    savings = round(baseline - llm_monthly, 2)

    budget = extracted_fields.get("monthly_budget_usd")
    within = None
    if budget:
        within = total <= float(budget)

    assumptions = []
    if str(extracted_fields.get("daily_requests", "unknown")) == "unknown":
        assumptions.append(f"Assumed {daily_req:,} requests/day based on {triage.get('classification','Moderate')} complexity")
    if str(extracted_fields.get("avg_input_tokens", "unknown")) == "unknown":
        assumptions.append(f"Assumed {avg_in} input tokens per request")
    if str(extracted_fields.get("avg_output_tokens", "unknown")) == "unknown":
        assumptions.append(f"Assumed {avg_out} output tokens per request")

    num_users = extracted_fields.get("number_of_users")
    cost_per_user = round(total / num_users, 2) if num_users and int(str(num_users)) > 0 else None

    infra_items = {
        "AWS": [
            {"item": "Lambda invocations (1M+)", "monthly_usd": 2.00},
            {"item": "API Gateway (1M calls)", "monthly_usd": 3.50},
            {"item": "S3 storage (10GB)", "monthly_usd": 0.23},
            {"item": "DynamoDB reads/writes", "monthly_usd": 5.00},
            {"item": "CloudWatch logs", "monthly_usd": 1.50},
            {"item": "Data transfer", "monthly_usd": 16.27},
        ],
        "GCP": [
            {"item": "Cloud Run (1M requests)", "monthly_usd": 3.20},
            {"item": "Cloud Endpoints", "monthly_usd": 0.00},
            {"item": "Cloud Storage (10GB)", "monthly_usd": 0.20},
            {"item": "Firestore reads/writes", "monthly_usd": 4.00},
            {"item": "Cloud Monitoring", "monthly_usd": 0.00},
            {"item": "Data transfer", "monthly_usd": 14.60},
        ],
        "Azure": [
            {"item": "Container Apps (1M requests)", "monthly_usd": 4.00},
            {"item": "API Management (1M calls)", "monthly_usd": 3.50},
            {"item": "Blob Storage (10GB)", "monthly_usd": 0.20},
            {"item": "Cosmos DB requests", "monthly_usd": 6.00},
            {"item": "Azure Monitor", "monthly_usd": 2.00},
            {"item": "Data transfer", "monthly_usd": 15.30},
        ],
    }

    items = [{"item": f"{best_model['name']} (LLM API calls)", "monthly_usd": llm_monthly}]
    items.extend(infra_items.get(cloud, infra_items["AWS"]))

    return {
        "llm_cost_monthly": llm_monthly,
        "llm_cost_per_1k_requests": cost_per_1k,
        "llm_cost_per_user": cost_per_user,
        "cloud_infra_cost_monthly": cloud_infra,
        "total_estimated_monthly": total,
        "baseline_comparison": baseline,
        "estimated_savings": savings,
        "assumptions": assumptions,
        "cost_breakdown_items": items,
    }, within


def _build_compliance_flags(extracted_fields: dict, cloud: str, region: str) -> tuple[list[dict], list[str]]:
    """Build compliance check flags and security recommendations."""
    data_sens = extracted_fields.get("data_sensitivity", "none").lower()
    standards = [s.upper() for s in extracted_fields.get("compliance_standards", [])]
    compliance_region = extracted_fields.get("compliance_region", "").lower()

    flags = []

    # GDPR check
    if "eu" in compliance_region or "GDPR" in standards:
        eu_regions = ["eu-west", "eu-central", "europe-west", "westeurope", "germanywest"]
        in_eu = any(r in region.lower() for r in eu_regions)
        flags.append({
            "flag": "GDPR data residency",
            "status": "pass" if in_eu else "warning",
            "detail": f"{'Selected EU region ensures GDPR data residency.' if in_eu else 'Non-EU region selected. For strict GDPR, consider an EU region.'}",
            "note": "" if in_eu else "Switch to eu-west-1 (AWS), europe-west1 (GCP), or westeurope (Azure)."
        })

    # HIPAA check
    if "HIPAA" in standards or data_sens == "critical":
        hipaa_certified = cloud in ("AWS", "Azure")
        flags.append({
            "flag": "HIPAA compliance",
            "status": "pass" if hipaa_certified else "warning",
            "detail": f"{cloud} {'is HIPAA eligible with a signed BAA.' if hipaa_certified else 'does not have native HIPAA BAA — consider AWS or Azure.'}",
            "note": "" if hipaa_certified else "AWS and Azure offer HIPAA Business Associate Agreements (BAA)."
        })

    # SOC2 check
    if "SOC2" in standards or data_sens in ("high", "critical"):
        flags.append({
            "flag": "SOC2 Type II",
            "status": "pass",
            "detail": f"{cloud} is SOC2 Type II certified across its primary regions.",
            "note": ""
        })

    # PII check
    if data_sens in ("medium", "high", "critical"):
        flags.append({
            "flag": "PII handling",
            "status": "warning" if data_sens == "medium" else "pass",
            "detail": "Ensure personal data is encrypted at rest and in transit. Enable audit logging.",
            "note": "Enable KMS encryption on storage and databases."
        })

    # Data in transit
    flags.append({
        "flag": "Encryption in transit (TLS)",
        "status": "pass",
        "detail": f"All {cloud} services use TLS 1.2+ for data in transit by default.",
        "note": ""
    })

    # Security recommendations
    _llm_svc_name = {"AWS": "Bedrock", "GCP": "Vertex AI", "Azure": "Azure OpenAI"}.get(cloud, "LLM service")
    security_recs = [
        f"Enable VPC endpoint for {_llm_svc_name} to route traffic privately",
        "Use a secrets manager for all API keys — never hardcode credentials",
        "Enable audit logging and set up alerts for anomalous usage patterns",
        "Apply least-privilege IAM roles — each service gets only what it needs",
        "Set a monthly budget alert at 80% of your limit to prevent runaway costs",
    ]

    if data_sens in ("high", "critical"):
        security_recs.append("Enable encryption at rest using customer-managed keys (CMK)")
        security_recs.append("Implement field-level encryption for PII fields in the database")

    return flags, security_recs


def _smart_fallback_recommendation(
    extracted_fields: dict,
    triage: dict,
    compliant_options: list[dict],
    description: str = "",
    forced_model: str | None = None,
    forced_cloud: str | None = None,
) -> dict:
    """
    Comprehensive rule-based recommendation generator.
    Generates all 8 guidebook sections locally without any LLM call.
    """
    description_lower = description.lower()
    budget_limit = _parse_budget(extracted_fields)
    all_models = get_all_models()

    # Score all models
    scored: list[tuple[float, float, dict]] = []
    for model in all_models:
        score, monthly_cost = _score_model(model, extracted_fields, triage, budget_limit, description_lower)
        scored.append((score, monthly_cost, model))
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored or scored[0][0] < -100:
        scored.sort(key=lambda x: x[1])

    if forced_model:
        best_model = None
        for m in all_models:
            if m["name"].lower() == forced_model.lower():
                best_model = m
                break
        if not best_model:
            for m in all_models:
                if forced_model.lower() in m["name"].lower() or m["name"].lower() in forced_model.lower():
                    best_model = m
                    break
        if not best_model:
            best_model = scored[0][2]
    else:
        best_model = scored[0][2]

    # Recalculate cost based on best_model
    daily_req, avg_in, avg_out = _resolve_volume(extracted_fields, triage)
    in_cost = best_model["cost_per_1k_input_tokens"] * (avg_in / 1000) * daily_req * 30
    out_cost = best_model["cost_per_1k_output_tokens"] * (avg_out / 1000) * daily_req * 30
    best_cost = round(in_cost + out_cost, 2)

    if forced_cloud:
        cloud = forced_cloud
        cloud_lower = cloud.lower()
        if "gcp" in cloud_lower:
            cloud = "GCP"
            region = "us-central1 (Iowa, USA)"
        elif "azure" in cloud_lower:
            cloud = "Azure"
            region = "eastus (Virginia, USA)"
        else:
            cloud = "AWS"
            region = "us-east-1 (N. Virginia, USA)"

        compliance_region = extracted_fields.get("compliance_region", "").lower()
        if "eu" in compliance_region or "europe" in compliance_region:
            region_map = {"AWS": "eu-west-1 (Ireland, EU)", "GCP": "europe-west1 (Belgium, EU)", "Azure": "westeurope (Netherlands, EU)"}
            region = region_map.get(cloud, region)
        elif "india" in compliance_region:
            region_map = {"AWS": "ap-south-1 (Mumbai, India)", "GCP": "asia-south1 (Mumbai, India)", "Azure": "centralindia (Pune, India)"}
            region = region_map.get(cloud, region)
    else:
        cloud, region = _pick_cloud_for_model(best_model, extracted_fields, compliant_options)

    # Build rich alternatives with detailed comparison data
    alternatives = []
    seen = {best_model["name"]}

    # Pre-build service name maps per cloud for change diffs
    _cloud_service_map = {
        "AWS":   {"llm": "AWS Bedrock",   "compute": "AWS Lambda",         "storage": "Amazon S3",      "db": "DynamoDB",    "monitor": "CloudWatch"},
        "GCP":   {"llm": "Vertex AI",     "compute": "Cloud Run",           "storage": "Cloud Storage",  "db": "Firestore",  "monitor": "Cloud Monitoring"},
        "Azure": {"llm": "Azure OpenAI",  "compute": "Container Apps",      "storage": "Blob Storage",   "db": "Cosmos DB",  "monitor": "Azure Monitor"},
    }

    for alt_score, alt_cost, alt_model in scored[1:]:
        if alt_model["name"] in seen:
            continue
        seen.add(alt_model["name"])
        alt_cloud, alt_region = _pick_cloud_for_model(alt_model, extracted_fields, compliant_options)

        cost_diff_usd = round(alt_cost - best_cost, 2)
        cost_diff_pct = round((cost_diff_usd / max(best_cost, 0.01)) * 100, 1)
        diff_str = (f"+${cost_diff_usd:,.2f}/mo" if cost_diff_usd > 0 else f"-${abs(cost_diff_usd):,.2f}/mo")

        # Pros of switching: strengths the alt has that best doesn't
        best_strengths = set(s.lower() for s in best_model.get("strengths", []))
        pros_of_switching = [
            s for s in alt_model.get("strengths", [])
            if not any(bs in s.lower() or s.lower() in bs for bs in best_strengths)
        ][:3]
        if not pros_of_switching:
            pros_of_switching = alt_model.get("strengths", [])[:2]

        # Cons of switching: strengths the best has that alt doesn't
        alt_strengths = set(s.lower() for s in alt_model.get("strengths", []))
        cons_of_switching = [
            s for s in best_model.get("strengths", [])
            if not any(as_ in s.lower() or s.lower() in as_ for as_ in alt_strengths)
        ][:3]
        if not cons_of_switching:
            cons_of_switching = best_model.get("limitations", alt_model.get("limitations", []))[:2]

        # Changed services if cloud differs
        changed_services = []
        if alt_cloud != cloud:
            rec_svcs = _cloud_service_map.get(cloud, {})
            alt_svcs = _cloud_service_map.get(alt_cloud, {})
            for svc_key in ["llm", "compute", "storage", "db", "monitor"]:
                if rec_svcs.get(svc_key) and alt_svcs.get(svc_key) and rec_svcs[svc_key] != alt_svcs[svc_key]:
                    changed_services.append(f"{rec_svcs[svc_key]} → {alt_svcs[svc_key]}")

        # Performance trade-off using benchmarks
        perf_lines = []
        for bench_key, bench_label in [("benchmark_gpqa", "GPQA"), ("benchmark_swe", "SWE-Bench"), ("speed_tps", "Speed (t/s)")]:
            bv = best_model.get(bench_key)
            av = alt_model.get(bench_key)
            if bv and av:
                direction = "↑ higher" if av > bv else "↓ lower"
                perf_lines.append(f"{bench_label}: {av} vs {bv} ({direction})")
        performance_tradeoff = "; ".join(perf_lines) if perf_lines else f"Similar capability tier ({alt_model.get('tier', 'Unknown')} vs {best_model.get('tier', 'Unknown')})"

        alternatives.append({
            "model": alt_model["name"],
            "provider": alt_model.get("provider", ""),
            "tier": alt_model.get("tier", ""),
            "cloud": alt_cloud,
            "region": alt_region,
            "estimated_monthly_cost": round(alt_cost, 2),
            "cost_diff_usd": cost_diff_usd,
            "cost_diff_pct": cost_diff_pct,
            "trade_off": f"{alt_model['name']} is {diff_str} vs recommended. {'; '.join(alt_model.get('strengths', [])[:2])}.",
            "best_for": ', '.join(alt_model.get('best_for', [])[:2]),
            "pros_of_switching": pros_of_switching,
            "cons_of_switching": cons_of_switching,
            "changed_services": changed_services,
            "performance_tradeoff": performance_tradeoff,
            "benchmark_gpqa": alt_model.get("benchmark_gpqa"),
            "benchmark_swe": alt_model.get("benchmark_swe"),
            "speed_tps": alt_model.get("speed_tps"),
            "max_context": alt_model.get("max_context"),
        })
        if len(alternatives) >= 3:
            break

    task_type = extracted_fields.get("task_type", "unknown")
    team_expertise = extracted_fields.get("team_expertise", "unknown")
    data_sens = extracted_fields.get("data_sensitivity", "none")
    classification = triage.get("classification", "Moderate")

    # Build all sections
    cloud_services = _build_cloud_services(cloud, task_type, data_sens, classification)
    dev_guide = _build_development_guide(cloud, task_type, team_expertise, classification)
    arch_summary, arch_components, data_flow = _build_architecture(cloud, task_type, classification)
    cost_breakdown, within_budget = _build_cost_breakdown(extracted_fields, triage, best_model, cloud)
    compliance_flags, security_recs = _build_compliance_flags(extracted_fields, cloud, region)

    model_rationale = (
        f"**{best_model['name']}** by {best_model['provider']} was selected as the best match "
        f"for your {classification.lower()}-complexity use case.\n\n"
        f"**Why this model:** {'; '.join(best_model.get('strengths', [])[:3])}. "
        f"It excels at: {', '.join(best_model.get('best_for', [])[:3])}.\n\n"
        f"**Pricing:** ${best_model['cost_per_1k_input_tokens']}/1K input tokens, "
        f"${best_model['cost_per_1k_output_tokens']}/1K output tokens."
    )
    if budget_limit:
        within = cost_breakdown["total_estimated_monthly"] <= budget_limit
        model_rationale += f"\n\n**Budget:** Estimated ${cost_breakdown['total_estimated_monthly']:,.2f}/month {'✅ fits' if within else '⚠️ may exceed'} your ${budget_limit:,.0f} budget."

    # Evidence-based confidence scoring — penalise missing critical fields
    confidence = 40  # Base score
    ef_check = extracted_fields

    # Reward well-specified fields
    if str(ef_check.get("daily_requests", "unknown")).lower() not in ("unknown", "", "none"):
        confidence += 12
    else:
        confidence -= 8  # Penalty: unknown request volume

    budget_val = ef_check.get("monthly_budget_usd")
    budget_hint = str(ef_check.get("budget_hint", "unknown")).lower()
    if budget_val or (budget_hint not in ("unknown", "", "none")):
        confidence += 12
    else:
        confidence -= 8  # Penalty: no budget specified

    comp_region = str(ef_check.get("compliance_region", "unknown")).lower()
    if comp_region not in ("unknown", "", "global", "none"):
        confidence += 8
    else:
        confidence -= 5  # Penalty: vague compliance region

    task = str(ef_check.get("task_type", "unknown")).lower()
    if task not in ("unknown", "", "none"):
        confidence += 7
    else:
        confidence -= 4

    if str(ef_check.get("avg_input_tokens", "unknown")).lower() not in ("unknown", "", "none"):
        confidence += 5
    if str(ef_check.get("avg_output_tokens", "unknown")).lower() not in ("unknown", "", "none"):
        confidence += 5

    # Bonus: compliance standards explicitly listed
    if ef_check.get("compliance_standards"):
        confidence += 8

    # Bonus: data sensitivity specified
    ds = str(ef_check.get("data_sensitivity", "none")).lower()
    if ds not in ("none", "unknown", ""):
        confidence += 5

    # Clamp to realistic range
    confidence = min(88, max(30, confidence))

    return {
        # Section 1
        "recommended_model": best_model["name"],
        "model_provider": best_model.get("provider", ""),
        "model_rationale": model_rationale,
        "model_strengths": best_model.get("strengths", [])[:5],
        "model_limitations": best_model.get("limitations", [])[:2],
        # Section 2
        "recommended_cloud": cloud,
        "recommended_region": region,
        "region": region,
        "cloud_rationale": (
            f"{cloud} was selected based on your region preference "
            f"({'EU compliance' if 'eu' in extracted_fields.get('compliance_region','').lower() else 'cost and availability'}). "
            f"The {region} region provides the best balance of latency, compliance, and model availability."
        ),
        "cloud_services": cloud_services,
        # Section 3
        "cost_breakdown": cost_breakdown,
        "within_budget": within_budget,
        "estimated_monthly_cost": cost_breakdown["total_estimated_monthly"],
        "baseline_cost": cost_breakdown["baseline_comparison"],
        # Section 4
        "development_guide": dev_guide,
        # Section 5
        "architecture_summary": arch_summary,
        "architecture_components": arch_components,
        "data_flow": data_flow,
        # Section 6
        "compliance_flags": compliance_flags,
        "security_recommendations": security_recs,
        # Section 7
        "alternatives": alternatives,
        # Section 8
        "confidence_score": confidence,
        "confidence_reasoning": (
            f"Confidence is {'high' if confidence >= 75 else 'moderate'} based on "
            f"{'well-defined task type, compliance, and scale' if confidence >= 75 else 'limited information — providing estimated values for unknown fields'}."
        ),
        "missing_info_impact": (
            "; ".join(cost_breakdown.get("assumptions", [])) or "none"
        ),
        # Legacy
        "rationale": model_rationale,
    }


def _compute_baseline_cost(extracted_fields: dict, triage: dict) -> float:
    """Kept for backward compatibility."""
    daily_req, avg_in, avg_out = _resolve_volume(extracted_fields, triage)
    return round(
        daily_req * avg_in / 1000 * 0.005 * 30 +
        daily_req * avg_out / 1000 * 0.015 * 30, 2
    )
