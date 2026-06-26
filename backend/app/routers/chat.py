"""
Chat router — handles follow-up chatbot messages and questions about recommendations.
Has a comprehensive local fallback engine when Gemini API is unavailable.
"""

import logging
import json
import re
import httpx
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UseCase, Recommendation
from app.config import get_settings
from app.services.knowledge_base import get_all_models, get_all_cloud_providers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatPayload(BaseModel):
    use_case_id: int
    messages: List[ChatMessage]


class ChartDataPoint(BaseModel):
    name: str
    value: float


class ChartSchema(BaseModel):
    type: str
    title: str
    data: List[ChartDataPoint]


class ChatResponse(BaseModel):
    text: str
    chart: Optional[ChartSchema] = None
    suggested_model: Optional[str] = None
    suggested_cloud: Optional[str] = None


CHAT_SYSTEM_PROMPT = """You are the AI Advisor — an expert solution architect specializing in
AI/ML infrastructure, LLM selection, cloud architecture, and cost optimization.

The user has already received a full recommendation. You have full context of:
  - Their use case description and extracted requirements
  - The recommended model, cloud, and all 8 sections of the recommendation

Recommendation context:
- Original Use Case: {description}
- Extracted Fields: {extracted_fields}
- Complexity Triage: {triage_classification} (Reasoning: {triage_reasoning})
- Recommended Model: {recommended_model} by {model_provider} on {recommended_cloud} ({region})
- Estimated Monthly Cost: ${estimated_monthly_cost} (Baseline GPT-4o: ${baseline_cost})
- Estimated Savings: ${estimated_savings}
- Model Rationale: {model_rationale}
- Model Strengths: {model_strengths}
- Cloud Services: {cloud_services}
- Development Guide Phases: {dev_guide_phases}
- Architecture: {architecture_summary}
- Compliance: {compliance_summary}
- Alternatives: {alternatives_summary}
- Confidence Score: {confidence_score}/100

Your role is to answer follow-up questions like a senior engineer would:
  - Be specific, not generic
  - Reference exact numbers (costs, token counts, latency) from the recommendation context above
  - When comparing models, do NOT focus only on cost. You MUST compare key non-cost capabilities such as benchmarks (GPQA, SWE-Bench), context window size, latency/speed, strengths/limitations, and best use case fit.
  - When comparing cloud providers (AWS vs GCP vs Azure), focus strictly on cloud infrastructure, services stack, regional compliance certifications, SLAs, and infrastructure/compute cost differences. Do NOT mix LLM capabilities into cloud comparisons.
  - If the user asks about an alternative model or cloud, or expresses interest in switching, explain the differences and ask if they would like to switch their main recommendation. If so, populate the "suggested_model" and/or "suggested_cloud" fields in the JSON response.
  - If asked to compare options, produce a clear comparison table using markdown
  - If asked for a chart, return chart data in the chart field
  - If the user reveals new information (new budget, different scale, new requirement),
    incorporate it into your answer and note how it changes the recommendation
  - Never say "I don't know" — use the context above and your engineering knowledge

RESPONSE FORMAT:
Always return valid JSON:
{{
  "text": "Your full markdown-formatted answer here. If suggesting a switch, ask: 'Would you like to switch the recommendation to [Model/Cloud]?'",
  "chart": null,
  "suggested_model": "Claude Sonnet 4.6",
  "suggested_cloud": null
}}

Or with a chart and no suggestions:
{{
  "text": "Your markdown answer",
  "chart": {{
    "type": "bar",
    "title": "Monthly Cost Comparison",
    "data": [{{"name": "Model A", "value": 45.60}}, {{"name": "Model B", "value": 120.00}}]
  }},
  "suggested_model": null,
  "suggested_cloud": null
}}

Set suggested_model and suggested_cloud to null if not suggesting a switch.

Only include chart when the user explicitly asks for a graph/chart/comparison,
or when a visual would significantly improve the answer.

TEXT FORMAT (use markdown):
  - ## for section headings
  - **bold** for key terms and model/service names
  - Bullet lists for multiple items
  - `code blocks` for API examples, CLI commands, config snippets
  - Tables for comparisons

CHART GUIDELINES:
  bar  → comparing costs, token counts, or performance metrics across options
  pie  → showing distribution (cost breakdown by service, traffic split)

- Alternatives: {alternatives}

Full model knowledge base (all available models with pricing):
{model_kb}

You must answer ANY question the user has, including:
- Why a specific model was or was not recommended
- Exact cost estimation given token counts or request volumes the user provides
- Whether a specific model (e.g., Amazon Nova, GPT-4o, DeepSeek) would work for their use case
- Budget-based model recommendations
- Comparisons between models
- Latency, context window, compliance questions
- How to reduce costs

If the user asks about token costs, CALCULATE the exact cost using the pricing data.
Formula: (input_tokens / 1000) * input_price + (output_tokens / 1000) * output_price

Return ONLY valid JSON:
{{
  "text": "Your markdown response...",
  "chart": null,
  "suggested_model": null,
  "suggested_cloud": null
}}
"""

# ─── Comprehensive local chat engine ────────────────────────────────────────


ALL_MODELS: list[dict] = []
ALL_CLOUDS: list[dict] = []


def _lazy_load_kb():
    global ALL_MODELS, ALL_CLOUDS
    if not ALL_MODELS:
        ALL_MODELS = get_all_models()
        ALL_CLOUDS = get_all_cloud_providers()


def _find_model_by_name(name: str) -> dict | None:
    """
    Find a model by name using scored matching.
    Returns the BEST match — not just the first partial hit.
    Priority: exact → all-keywords-match → most-keywords-match → any-keyword-match
    Longer / more specific keywords (like 'sonnet', 'haiku', 'flash') score higher.
    """
    _lazy_load_kb()
    name_l = name.lower().strip()

    # 1. Exact match
    for m in ALL_MODELS:
        if m["name"].lower() == name_l:
            return m

    # 2. Full model name contained in query (e.g. "claude sonnet 4" in "why not claude sonnet 4?")
    for m in ALL_MODELS:
        if m["name"].lower() in name_l:
            return m

    # 3. Scored keyword match — score every model, return the highest
    # Only use meaningful keywords (len >= 4), ignore stop words
    stop_words = {"why", "not", "use", "what", "about", "tell", "with", "that", "this",
                  "would", "could", "should", "does", "much", "cost", "good", "best",
                  "model", "also", "like", "than", "more", "less", "compare", "show"}
    keywords = [
        kw for kw in re.split(r'\W+', name_l)
        if len(kw) >= 4 and kw not in stop_words
    ]

    if not keywords:
        return None

    scored: list[tuple[float, dict]] = []
    for m in ALL_MODELS:
        model_l = m["name"].lower()
        score = 0.0
        for kw in keywords:
            if kw in model_l:
                # Longer keywords are more specific → higher score
                score += len(kw) * 2
                # Exact word boundary bonus (e.g. "sonnet" matches "Sonnet" not "Sonnets...")
                if re.search(r'\b' + re.escape(kw) + r'\b', model_l):
                    score += len(kw)
        if score > 0:
            # Bonus: if ALL non-trivial keywords match, this is almost certainly the right model
            matched_all = all(kw in model_l for kw in keywords)
            if matched_all:
                score += 50
            scored.append((score, m))

    if not scored:
        return None

    # Return the model with the highest score
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]



def _calc_monthly_cost(model: dict, daily_req: int, input_tokens: int, output_tokens: int) -> float:
    in_cost = model["cost_per_1k_input_tokens"] * (input_tokens / 1000) * daily_req * 30
    out_cost = model["cost_per_1k_output_tokens"] * (output_tokens / 1000) * daily_req * 30
    return round(in_cost + out_cost, 4)


def _extract_numbers(text: str) -> list[int]:
    """Extract all integers from text."""
    return [int(n.replace(",", "")) for n in re.findall(r"[\d,]+", text) if n.replace(",", "").isdigit()]


def _build_cost_chart(models_costs: list[tuple[str, float]], title: str) -> ChartSchema:
    return ChartSchema(
        type="bar",
        title=title,
        data=[ChartDataPoint(name=name, value=cost) for name, cost in models_costs]
    )


def _get_local_chat_response(
    recommendation: Recommendation,
    use_case: UseCase,
    user_message: str,
    conversation_history: list,
) -> ChatResponse:
    """Comprehensive local chat engine — handles any user question intelligently."""
    _lazy_load_kb()
    msg = user_message.lower().strip()
    chart_data = None
    numbers = _extract_numbers(msg)

    # ── GUARDRAIL: off-topic filter ─────────────────────────────────────────
    OFF_TOPIC_PATTERNS = [
        r"\b(weather|cricket|football|soccer|sports|movie|recipe|cook|music|song|game|stock market|crypto|bitcoin|relationship|joke|poem|essay|story|novel|capital of|president|population|war|history of|news)\b",
        r"\b(translate|grammar|spell check|synonym|antonym|wikipedia|search for|who is|who was|what is the meaning|image of|generate image|kl rahul)\b",
    ]
    ON_TOPIC_KEYWORDS = [
        "model", "cloud", "aws", "gcp", "azure", "cost", "price", "budget", "token",
        "llm", "api", "deploy", "latency", "speed", "compliance", "gdpr", "hipaa",
        "region", "recommend", "alternative", "compare", "switch", "use case",
        "claude", "gpt", "gemini", "llama", "mistral", "openai", "anthropic", "google",
        "inference", "fine-tun", "embedding", "rag", "architecture", "serve", "scale",
        "request", "throughput", "context", "window", "saving", "cheap", "expensive",
        "bedrock", "vertex", "sagemaker", "certification", "soc2", "iso", "pii", "phi",
        "step", "setup", "develop", "implement", "build", "phase", "guide"
    ]
    CONVERSATIONAL_FILLERS = ["hi", "hello", "hey", "thanks", "thank you", "ok", "okay", "yes", "no", "sure", "correct", "agree", "test"]

    import re as _re_guard
    is_off_topic = any(_re_guard.search(p, msg) for p in OFF_TOPIC_PATTERNS)
    is_on_topic  = any(kw in msg for kw in ON_TOPIC_KEYWORDS)
    is_filler    = any(msg.startswith(f) or msg == f for f in CONVERSATIONAL_FILLERS)

    if (is_off_topic and not is_on_topic) or (not is_on_topic and not is_filler):
        return ChatResponse(
            text=(
                "### ⛔ Off-Topic Question Detected\n\n"
                "I'm your **AI Model & Cloud Advisor** — I only answer questions related to:\n"
                "- 🤖 AI model selection (Claude, GPT-4o, Gemini, Llama, Mistral…)\n"
                "- ☁️ Cloud platforms (AWS, GCP, Azure) — cost, compliance, architecture\n"
                "- 💰 Cost estimation, token pricing, budget planning\n"
                "- 🔒 Compliance (GDPR, HIPAA, SOC2, ISO 27001)\n"
                "- 🛠️ Development, deployment, and setup steps\n"
                "- ⚡ Latency, throughput, scalability\n\n"
                "**Try asking:**\n"
                "- *\"What are the steps of developing this?\"*\n"
                "- *\"Why not GPT-4o for my use case?\"*\n"
                "- *\"Compare Llama vs Claude Sonnet\"*\n"
                "- *\"What tools do I need on GCP?\"*"
            ),
            chart=None
        )
    # ────────────────────────────────────────────────────────────────────────

    rec_model_name = recommendation.recommended_model or ""
    rec_cloud = recommendation.recommended_cloud or "AWS"
    rec_region = recommendation.region or "us-east-1"
    rec_cost = float(recommendation.estimated_monthly_cost or 0)
    baseline_cost = float(recommendation.baseline_cost or 0)
    rationale = recommendation.rationale or ""
    alternatives = recommendation.alternatives or []
    savings = max(0, baseline_cost - rec_cost)

    # Parse actual parameters from database if available to avoid cost mismatching
    ef = use_case.extracted_fields or {}

    db_daily_r = 1000
    db_req = ef.get("daily_requests")
    if db_req:
        try:
            if isinstance(db_req, (int, float)):
                db_daily_r = int(db_req)
            else:
                nums = _extract_numbers(str(db_req))
                if nums:
                    db_daily_r = nums[0]
        except Exception:
            pass

    db_input_t = 500
    db_in = ef.get("avg_input_tokens")
    if db_in:
        try:
            if isinstance(db_in, (int, float)):
                db_input_t = int(db_in)
            else:
                nums = _extract_numbers(str(db_in))
                if nums:
                    db_input_t = nums[0]
        except Exception:
            pass

    db_output_t = 300
    db_out = ef.get("avg_output_tokens")
    if db_out:
        try:
            if isinstance(db_out, (int, float)):
                db_output_t = int(db_out)
            else:
                nums = _extract_numbers(str(db_out))
                if nums:
                    db_output_t = nums[0]
        except Exception:
            pass

    # Conversational memory: Scan history to find active model and cloud if not explicit in current message
    mentioned_model = _find_model_by_name(msg)
    is_implicit_model = False
    if not mentioned_model:
        # scan history backwards for mentioned model
        for prev_msg in reversed(conversation_history[:-1]):
            found = _find_model_by_name(prev_msg.content)
            if found:
                mentioned_model = found
                is_implicit_model = True
                break

    asked_cloud = None
    for c in ["aws", "gcp", "azure"]:
        if c in msg:
            asked_cloud = c.upper()
            break
    if not asked_cloud:
        # scan history backwards for cloud provider
        for prev_msg in reversed(conversation_history[:-1]):
            prev_content = prev_msg.content.lower()
            for c in ["aws", "gcp", "azure"]:
                if c in prev_content:
                    asked_cloud = c.upper()
                    break
            if asked_cloud:
                break

    # ── 1. Token / cost calculation questions ───────────────────────────────
    if any(w in msg for w in ["token", "per request", "per query", "cost per", "how much per"]):
        # Try to extract token count and request volume from message, fallback to DB values
        input_t = db_input_t
        output_t = db_output_t
        daily_r = db_daily_r

        t_match = re.search(r"(\d[\d,]*)\s*(?:input|in)?\s*token", msg)
        if t_match:
            input_t = int(t_match.group(1).replace(",", ""))
        o_match = re.search(r"(\d[\d,]*)\s*(?:output|out)\s*token", msg)
        if o_match:
            output_t = int(o_match.group(1).replace(",", ""))
        r_match = re.search(r"(\d[\d,]*)\s*(?:request|quer|call|api)", msg)
        if r_match:
            try:
                daily_r = int(r_match.group(1).replace(",", ""))
                if "month" in msg:
                    daily_r = daily_r // 30
            except ValueError:
                pass
        elif numbers:
            if numbers[0] > 1000:
                daily_r = numbers[0]
            elif numbers[0] > 10:
                input_t = numbers[0]

        # Find model to calculate for
        target_model_data = _find_model_by_name(rec_model_name)
        target_name = rec_model_name

        # Check if user asked about a specific other model
        for m in ALL_MODELS:
            if m["name"].lower() in msg:
                target_model_data = m
                target_name = m["name"]
                break

        models_to_compare = []
        if target_model_data:
            models_to_compare.append(target_model_data)

        # Add top 4 cheapest for comparison
        for m in sorted(ALL_MODELS, key=lambda x: x["cost_per_1k_input_tokens"])[:4]:
            if m["name"] not in [x["name"] for x in models_to_compare]:
                models_to_compare.append(m)

        cost_rows = []
        for m in models_to_compare[:5]:
            c = _calc_monthly_cost(m, daily_r, input_t, output_t)
            cost_rows.append((m["name"], c))

        cost_rows.sort(key=lambda x: x[1])

        target_cost = _calc_monthly_cost(target_model_data, daily_r, input_t, output_t) if target_model_data else rec_cost
        per_req_in = (target_model_data["cost_per_1k_input_tokens"] * input_t / 1000) if target_model_data else 0
        per_req_out = (target_model_data["cost_per_1k_output_tokens"] * output_t / 1000) if target_model_data else 0
        per_req = per_req_in + per_req_out

        text = (
            f"### 💰 Cost Calculation for **{target_name}**\n\n"
            f"**Your parameters:**\n"
            f"- Input tokens per request: **{input_t:,}**\n"
            f"- Output tokens per request: **{output_t:,}**\n"
            f"- Daily requests: **{daily_r:,}** ({daily_r * 30:,}/month)\n\n"
            f"**Per-request cost:** `${per_req:.6f}`\n"
            f"**Estimated monthly cost: `${target_cost:,.2f}`**\n\n"
            f"### Comparison with alternatives:\n"
            + "\n".join([f"- **{name}**: ${cost:,.2f}/month" for name, cost in cost_rows])
            + f"\n\n*Cheapest option: **{cost_rows[0][0]}** at ${cost_rows[0][1]:,.2f}/month*"
        )
        chart_data = _build_cost_chart(cost_rows[:6], f"Monthly Cost Comparison ({input_t} in / {output_t} out tokens, {daily_r:,} req/day)")
        return ChatResponse(text=text, chart=chart_data)

    # ── 2. Budget-based recommendation questions ─────────────────────────────
    if any(w in msg for w in ["budget", "afford", "within", "under $", "less than $", "max $", "maximum"]):
        budget = None
        b_match = re.search(r"\$?([\d,]+)", msg)
        if b_match:
            try:
                budget = float(b_match.group(1).replace(",", ""))
            except ValueError:
                pass

        if budget:
            input_t = db_input_t
            output_t = db_output_t
            daily_r = db_daily_r

            affordable = []
            for m in ALL_MODELS:
                cost = _calc_monthly_cost(m, daily_r, input_t, output_t)
                if cost <= budget:
                    affordable.append((m, cost))

            affordable.sort(key=lambda x: x[1], reverse=True)  # Best value within budget

            if affordable:
                best_m, best_c = affordable[0]
                text = (
                    f"### Models Within Your ${budget:,.0f}/month Budget\n\n"
                    f"**Best recommendation: {best_m['name']}** by {best_m['provider']} — **${best_c:,.2f}/month**\n\n"
                    f"*Why:* {'; '.join(best_m.get('strengths', [])[:2])}. "
                    f"Best for: {', '.join(best_m.get('best_for', [])[:2])}.\n\n"
                    f"**All models within your budget:**\n"
                    + "\n".join([f"- **{m['name']}** ({m['provider']}, {m['tier']}): ${c:,.2f}/month" for m, c in affordable])
                    + f"\n\n*Estimated at {input_t} input + {output_t} output tokens, {daily_r:,} requests/day*"
                )
                chart_data = _build_cost_chart(
                    [(m["name"], c) for m, c in affordable[:8]],
                    f"Models Within ${budget:,.0f}/month Budget"
                )
            else:
                cheapest_m = min(ALL_MODELS, key=lambda x: x["cost_per_1k_input_tokens"])
                cheapest_cost = _calc_monthly_cost(cheapest_m, daily_r, input_t, output_t)
                text = (
                    f"### Budget Alert: ${budget:,.0f}/month\n\n"
                    f"At your current scale ({daily_r:,} req/day, {input_t} in + {output_t} out tokens), "
                    f"no models fit within ${budget:,.0f}/month.\n\n"
                    f"**Closest option:** {cheapest_m['name']} at **${cheapest_cost:,.2f}/month**\n\n"
                    f"**To fit your budget, you could:**\n"
                    f"- Reduce daily requests to ~{int(budget / (cheapest_cost / max(daily_r, 1))):,}/day\n"
                    f"- Use shorter prompts (fewer input tokens)\n"
                    f"- Cache frequent responses to reduce API calls"
                )
        else:
            text = "Please specify your monthly budget (e.g., 'What models fit within $500/month?') and I'll give you a precise recommendation."

        return ChatResponse(text=text, chart=chart_data)

    # ── 3. Questions about a specific model (e.g., "would Nova work?", "why not?") ──────────
    is_rec_model = mentioned_model and rec_model_name and mentioned_model["name"].lower() == rec_model_name.lower()
    model_keywords = ["work", "use", "good", "fit", "suitable", "better", "compare", "vs", "versus",
                      "why not", "why", "suit", "compatibility", "run", "optimal", "limitations",
                      "weakness", "switch", "if i use", "instead", "what about", "what if"]

    if mentioned_model and not is_rec_model and any(w in msg for w in model_keywords):
        rec_model_data = _find_model_by_name(rec_model_name)
        input_t = db_input_t
        output_t = db_output_t
        daily_r = db_daily_r

        mentioned_cost = _calc_monthly_cost(mentioned_model, daily_r, input_t, output_t)
        rec_cost_calc = _calc_monthly_cost(rec_model_data, daily_r, input_t, output_t) if rec_model_data else rec_cost
        cost_diff = mentioned_cost - rec_cost_calc
        cost_diff_str = f"${abs(cost_diff):,.2f} {'more' if cost_diff > 0 else 'less'} expensive"

        pros = mentioned_model.get("strengths", [])
        cons = mentioned_model.get("limitations", [])
        best_for = mentioned_model.get("best_for", [])

        # Check fit with use case
        task_type = (use_case.extracted_fields or {}).get("task_type", "").lower()
        fit_score = sum(1 for bf in best_for if bf.lower() in task_type or task_type in bf.lower())
        classification = use_case.triage_classification or "Moderate"
        fit_label = "✅ Good fit" if fit_score > 0 else "⚠️ Possible fit" if mentioned_model["tier"] != "Small" else "⚠️ May be underpowered"

        # Build which cloud to use for this model
        alt_cloud = asked_cloud or rec_cloud
        for c in ALL_CLOUDS:
            if mentioned_model["name"] in c.get("supported_models", []):
                alt_cloud = c["name"]
                break

        # Figure out service changes if cloud changes
        _cloud_svc_map = {
            "AWS":   {"llm": "AWS Bedrock",   "compute": "Lambda",         "storage": "S3",           "db": "DynamoDB"},
            "GCP":   {"llm": "Vertex AI",     "compute": "Cloud Run",       "storage": "Cloud Storage","db": "Firestore"},
            "Azure": {"llm": "Azure OpenAI",  "compute": "Container Apps",  "storage": "Blob Storage", "db": "Cosmos DB"},
        }
        svc_changes = []
        if alt_cloud != rec_cloud:
            r_svcs = _cloud_svc_map.get(rec_cloud, {})
            a_svcs = _cloud_svc_map.get(alt_cloud, {})
            for k in ["llm", "compute", "storage", "db"]:
                if r_svcs.get(k) and a_svcs.get(k):
                    svc_changes.append(f"`{r_svcs[k]}` → `{a_svcs[k]}`")

        text = (
            f"### {mentioned_model['name']} — Compatibility Analysis\n\n"
            f"**Provider:** {mentioned_model['provider']} | **Tier:** {mentioned_model['tier']} | "
            f"**Context:** {mentioned_model.get('max_context',0):,} tokens | "
            f"**Deploy on:** {alt_cloud}\n\n"
            f"**For your {classification} use case:** {fit_label}\n\n"
            f"### 💰 Cost Impact\n"
            f"| | Monthly Cost |\n|---|---|\n"
            f"| 🔵 **Current ({rec_model_name})** | **${rec_cost_calc:,.2f}** |\n"
            f"| 🔴 **Switch to {mentioned_model['name']}** | **${mentioned_cost:,.2f}** |\n"
            f"| **Difference** | **{'+' if cost_diff > 0 else ''}{cost_diff:,.2f}/mo** |\n\n"
            f"### ✅ Pros of Switching\n"
            + "\n".join([f"- {p}" for p in pros[:4]]) + "\n\n"
            f"### ❌ Cons of Switching\n"
            + "\n".join([f"- {c}" for c in cons[:3]]) + "\n\n"
        )
        if svc_changes:
            text += f"### 🔄 Cloud Service Changes ({rec_cloud} → {alt_cloud})\n" + "\n".join([f"- {s}" for s in svc_changes]) + "\n\n"
        text += (
            f"**Best for:** {', '.join(best_for[:4])}\n\n"
            f"**Verdict:** {'Switching is recommended' if cost_diff < 0 and fit_score > 0 else 'Current recommendation is still optimal' if fit_score == 0 else 'Viable alternative — switch if the strengths above match your priorities'}.\n\n"
            f"Would you like to switch your primary recommended model to **{mentioned_model['name']}**?"
        )
        chart_data = _build_cost_chart(
            [(rec_model_name, rec_cost_calc), (mentioned_model["name"], mentioned_cost)],
            "Cost Comparison: Monthly Estimate ($)"
        )
        return ChatResponse(text=text, chart=chart_data, suggested_model=mentioned_model["name"])

    # ── 3b. Side-by-side model COMPARISON ("compare X vs Y") ──────────────────
    compare_pattern = re.search(
        r'(?:compare|vs\.?|versus|difference between)\s+([a-z0-9 .\-]+?)\s+(?:vs\.?|versus|and|or|compared to)\s+([a-z0-9 .\-]+)',
        msg
    )
    if compare_pattern or ("compare" in msg and mentioned_model):
        models_to_compare: list[dict] = []
        if compare_pattern:
            m1 = _find_model_by_name(compare_pattern.group(1).strip())
            m2 = _find_model_by_name(compare_pattern.group(2).strip())
            if m1: models_to_compare.append(m1)
            if m2 and (not m1 or m2["name"] != m1["name"]): models_to_compare.append(m2)
        if not models_to_compare and mentioned_model:
            models_to_compare.append(mentioned_model)
        rec_m_data = _find_model_by_name(rec_model_name)
        if rec_m_data and (not models_to_compare or rec_m_data["name"] not in [m["name"] for m in models_to_compare]):
            models_to_compare.insert(0, rec_m_data)

        if len(models_to_compare) >= 2:
            input_t = db_input_t
            output_t = db_output_t
            daily_r = db_daily_r

            text = f"### 📊 Model Comparison\n*Estimated at {input_t} input + {output_t} output tokens, {daily_r:,} req/day*\n\n"
            text += "| Attribute | " + " | ".join([f"**{m['name']}**" for m in models_to_compare]) + " |\n"
            text += "|---|" + "---|" * len(models_to_compare) + "\n"
            text += "| Provider | " + " | ".join([m['provider'] for m in models_to_compare]) + " |\n"
            text += "| Tier | " + " | ".join([m['tier'] for m in models_to_compare]) + " |\n"

            costs = [_calc_monthly_cost(m, daily_r, input_t, output_t) for m in models_to_compare]
            text += "| Monthly Cost | " + " | ".join([f"**${c:,.2f}**" for c in costs]) + " |\n"
            text += "| Input $/1K tokens | " + " | ".join([f"${m['cost_per_1k_input_tokens']}" for m in models_to_compare]) + " |\n"
            text += "| Output $/1K tokens | " + " | ".join([f"${m['cost_per_1k_output_tokens']}" for m in models_to_compare]) + " |\n"
            text += "| Context Window | " + " | ".join([f"{m.get('max_context',0):,}" for m in models_to_compare]) + " |\n"

            # Benchmark rows if data available
            if any(m.get("benchmark_gpqa") for m in models_to_compare):
                text += "| GPQA Benchmark | " + " | ".join([str(m.get('benchmark_gpqa', 'N/A')) for m in models_to_compare]) + " |\n"
            if any(m.get("benchmark_swe") for m in models_to_compare):
                text += "| SWE-Bench | " + " | ".join([str(m.get('benchmark_swe', 'N/A')) for m in models_to_compare]) + " |\n"

            text += "| Strengths | " + " | ".join(['; '.join(m.get('strengths', [])[:2]) for m in models_to_compare]) + " |\n"
            text += "| Weaknesses | " + " | ".join(['; '.join(m.get('limitations', [])[:2]) for m in models_to_compare]) + " |\n\n"

            chart_rows = [(m["name"], _calc_monthly_cost(m, daily_r, input_t, output_t)) for m in models_to_compare]
            chart_data = _build_cost_chart(chart_rows, "Model Cost Comparison ($/mo)")
            return ChatResponse(text=text, chart=chart_data)

    # ── 4. Cloud provider switch / cost / services questions ───────────────────
    cloud_keywords = ["aws", "gcp", "azure", "cloud", "complian", "gdpr", "hipaa", "pii", "phi",
                      "region", "data residen", "certif", "switch", "migrate", "if i use",
                      "tools", "services", "what tools", "infrastructure", "infra"]
    if any(w in msg for w in cloud_keywords):
        if asked_cloud and asked_cloud.upper() != rec_cloud.upper():
            # ── Full cloud-switch recalculation ──────────────────────────────
            target_cloud = asked_cloud.upper()

            # Find the best model available on the target cloud
            target_cloud_data = next((c for c in ALL_CLOUDS if c["name"].upper() == target_cloud), None)
            supported = target_cloud_data.get("supported_models", []) if target_cloud_data else []
            best_model_for_cloud = None
            for m in ALL_MODELS:
                if m["name"] in supported:
                    best_model_for_cloud = m
                    break
            if not best_model_for_cloud and ALL_MODELS:
                best_model_for_cloud = ALL_MODELS[0]

            input_t = db_input_t
            output_t = db_output_t
            daily_r = db_daily_r

            new_cost = _calc_monthly_cost(best_model_for_cloud, daily_r, input_t, output_t) if best_model_for_cloud else rec_cost

            # Infra costs per cloud
            infra_cost = {"AWS": 31.27, "GCP": 22.00, "Azure": 31.00}.get(target_cloud, 25.0)
            rec_infra_cost = {"AWS": 31.27, "GCP": 22.00, "Azure": 31.00}.get(rec_cloud, 28.0)
            new_total = round(new_cost + infra_cost, 2)
            rec_total = rec_cost
            delta = round(new_total - rec_total, 2)
            delta_str = f"+${delta:,.2f}/mo more expensive" if delta > 0 else f"${abs(delta):,.2f}/mo cheaper"

            # Service stacks per cloud
            service_stacks = {
                "AWS":   ["AWS Bedrock (LLM inference)", "AWS Lambda (serverless compute)",
                          "Amazon S3 (object storage)", "DynamoDB (NoSQL DB)",
                          "CloudWatch (monitoring)", "API Gateway (routing)", "IAM (access control)"],
                "GCP":   ["Vertex AI (LLM inference)", "Cloud Run (serverless compute)",
                          "Cloud Storage (object storage)", "Firestore (NoSQL DB)",
                          "Cloud Monitoring (observability)", "Cloud Endpoints (API)", "IAM (access control)"],
                "Azure": ["Azure OpenAI Service (LLM inference)", "Container Apps (serverless compute)",
                          "Blob Storage (object storage)", "Cosmos DB (NoSQL DB)",
                          "Azure Monitor (observability)", "API Management (routing)", "Entra ID (access control)"],
            }
            new_services = service_stacks.get(target_cloud, service_stacks["AWS"])
            old_services = service_stacks.get(rec_cloud, service_stacks["AWS"])

            # Cloud pros/cons
            cloud_pros_cons = {
                "AWS":   {"pros": ["Widest model marketplace (Bedrock)", "Largest global region footprint", "Strongest enterprise compliance (FedRAMP, HIPAA, SOC2)", "Deepest ML tooling (SageMaker)"],
                          "cons": ["Higher infra cost vs GCP", "Steeper learning curve", "Vendor lock-in risk"]},
                "GCP":   {"pros": ["Lowest infra cost", "Best Gemini/PaLM native support", "Superior data analytics (BigQuery)", "Best Kubernetes (GKE)"],
                          "cons": ["Smaller model marketplace", "Fewer enterprise compliance certifications vs AWS", "Smaller support community"]},
                "Azure": {"pros": ["Native Microsoft 365 / Teams integration", "Best for enterprises using Windows Server / Active Directory", "Strong hybrid cloud (Azure Arc)", "Azure OpenAI exclusive access"],
                          "cons": ["Higher cost for pure cloud-native apps", "Can be complex to configure", "Less flexible pricing vs GCP"]},
            }
            t_pros = cloud_pros_cons.get(target_cloud, {}).get("pros", [])
            t_cons = cloud_pros_cons.get(target_cloud, {}).get("cons", [])

            # Region selection
            new_region = "us-east-1" if target_cloud == "AWS" else "us-central1" if target_cloud == "GCP" else "eastus"
            if target_cloud_data:
                for r in target_cloud_data.get("regions", []):
                    new_region = r.get("id", new_region)
                    break

            text = (
                f"## 🔄 Cloud Switch: {rec_cloud} → {target_cloud}\n\n"
                f"### 💰 Estimated Cost on {target_cloud}\n"
                f"| | {rec_cloud} (Current) | {target_cloud} (Proposed) |\n|---|---|---|\n"
                f"| LLM API Cost | ${rec_cost:,.2f}/mo | ${new_cost:,.2f}/mo |\n"
                f"| Cloud Infra | ~${rec_infra_cost:,.2f}/mo | ~${infra_cost:,.2f}/mo |\n"
                f"| **Total** | **${rec_total:,.2f}/mo** | **${new_total:,.2f}/mo** |\n"
                f"| **Difference** | | **{delta_str}** |\n\n"
                f"**Recommended model on {target_cloud}:** {best_model_for_cloud['name'] if best_model_for_cloud else 'N/A'} ({new_region})\n\n"
                f"### ⚙️ Service Stack Changes\n"
                f"| Current ({rec_cloud}) | Switch to ({target_cloud}) |\n|---|---|\n"
                + "\n".join([f"| {o} | {n} |" for o, n in zip(old_services, new_services)]) + "\n\n"
                f"### ✅ Why Switch to {target_cloud}?\n"
                + "\n".join([f"- {p}" for p in t_pros]) + "\n\n"
                f"### ❌ Trade-offs of Switching\n"
                + "\n".join([f"- {c}" for c in t_cons]) + "\n\n"
                f"### 🛠️ Migration Steps\n"
                f"1. Set up {target_cloud} account and enable {'Bedrock' if target_cloud=='AWS' else 'Vertex AI' if target_cloud=='GCP' else 'Azure OpenAI Service'}\n"
                f"2. Provision {new_region} region resources\n"
                f"3. Update API endpoints and authentication keys\n"
                f"4. Migrate data to {'S3' if target_cloud=='AWS' else 'Cloud Storage' if target_cloud=='GCP' else 'Blob Storage'}\n"
                f"5. Redirect traffic incrementally (use blue/green deployment)\n"
                f"6. Validate compliance certifications for {new_region}\n\n"
                f"Would you like to switch your primary recommended cloud provider to **{target_cloud}**?"
            )
            chart_data = _build_cost_chart(
                [(f"{rec_cloud} (Current)", rec_total), (f"{target_cloud} (Proposed)", new_total)],
                f"Monthly Cost: {rec_cloud} vs {target_cloud}"
            )
            return ChatResponse(text=text, chart=chart_data, suggested_cloud=target_cloud)

        elif asked_cloud and asked_cloud.upper() == rec_cloud.upper():
            text = (
                f"### Cloud Deployment: **{rec_cloud}**\n\n"
                f"Your recommendation is already configured for deployment on **{rec_cloud}** (region **{rec_region}**).\n\n"
                f"**Why {rec_cloud} is optimal for this deployment:**\n"
            )
            for cloud_item in ALL_CLOUDS:
                if cloud_item["name"].lower() == rec_cloud.lower():
                    text += "\n".join([f"- **Strength:** {s}" for s in cloud_item.get("strengths", [])[:4]])
                    break
            return ChatResponse(text=text, chart=None)

        ef = use_case.extracted_fields or {}
        text = (
            f"### Compliance & Data Residency\n\n"
            f"**Your use case profile:**\n"
            f"- Data sensitivity: **{ef.get('data_sensitivity', 'Not specified')}**\n"
            f"- Compliance region: **{ef.get('compliance_region', 'Not specified')}**\n\n"
            f"**Recommended deployment:** {rec_model_name} on {rec_cloud}, region **{rec_region}**\n\n"
            f"**Available compliance certifications for {rec_cloud} {rec_region}:**\n"
        )
        for cloud_item in ALL_CLOUDS:
            if cloud_item["name"].lower() == rec_cloud.lower():
                for region_item in cloud_item["regions"]:
                    if region_item.get("id", "") in rec_region:
                        certs = region_item.get("compliance", [])
                        text += "\n".join([f"- ✅ {c}" for c in certs])
                        break
        text += (
            f"\n\n**For HIPAA:** AWS us-east-1, Azure eastus, GCP us-central1 are certified.\n"
            f"**For GDPR:** Choose any EU region (AWS eu-west-1, Azure westeurope, GCP europe-west1).\n"
            f"**For maximum privacy:** Consider self-hosted open-source models (Llama, DeepSeek, Qwen) "
            f"where data never leaves your infrastructure."
        )
        return ChatResponse(text=text, chart=None)

    # ── 5. Cost / savings questions ─────────────────────────────────────────
    if any(w in msg for w in ["cost", "price", "spend", "saving", "expensive", "cheap", "cheaper", "how much"]):
        alt_costs = []
        if alternatives:
            for alt in alternatives[:3]:
                if isinstance(alt, dict):
                    alt_costs.append((f"{alt.get('model', 'Alt')} ({alt.get('cloud', '')})", float(alt.get("estimated_monthly_cost", 0))))

        text = (
            f"### 💰 Cost Breakdown\n\n"
            f"**Recommended: {rec_model_name}** on {rec_cloud} ({rec_region})\n"
            f"- Estimated monthly cost: **${rec_cost:,.2f}**\n"
            f"- Baseline (GPT-4o equivalent): **${baseline_cost:,.2f}**\n"
            f"- **You save: ${savings:,.2f}/month ({round(savings / max(baseline_cost, 1) * 100)}%)**\n\n"
        )
        if alt_costs:
            text += "**Alternative options:**\n"
            for name, cost in alt_costs:
                diff = cost - rec_cost
                text += f"- {name}: **${cost:,.2f}/month** ({'+' if diff > 0 else ''}{diff:,.2f} vs recommended)\n"
            chart_data = _build_cost_chart(
                [(rec_model_name, rec_cost), ("Baseline GPT-4o", baseline_cost)] + alt_costs,
                "Monthly Cost Comparison ($)"
            )
        text += (
            f"\n💡 **To reduce costs further:**\n"
            f"- Use **Amazon Nova Micro** (~${_calc_monthly_cost(_find_model_by_name('Amazon Nova Micro') or ALL_MODELS[0], 10_000, 200, 100):,.2f}/mo) for simple tasks\n"
            f"- Use **Gemini 1.5 Flash** (~${_calc_monthly_cost(_find_model_by_name('Gemini 1.5 Flash') or ALL_MODELS[0], 10_000, 200, 100):,.2f}/mo) for highest volume\n"
            f"- Cache frequent responses to reduce API call count"
        )
        return ChatResponse(text=text, chart=chart_data)

    # ── 6. Why was this model recommended? ──────────────────────────────────
    if any(w in msg for w in ["why", "reason", "explain", "how", "decision", "choose", "chose"]):
        rec_model_data = _find_model_by_name(rec_model_name)
        classification = use_case.triage_classification or "Moderate"
        text = (
            f"### Why **{rec_model_name}** Was Recommended\n\n"
            f"**1. Complexity match:** Your use case was classified as **{classification}**. "
            f"{rec_model_name} ({rec_model_data.get('tier', 'Medium') if rec_model_data else 'Medium'} tier) "
            f"is the right capability level — not over-engineered, not underpowered.\n\n"
            f"**2. Cost efficiency:** At ${rec_cost:,.2f}/month vs baseline ${baseline_cost:,.2f}/month, "
            f"you save **${savings:,.2f}/month** ({round(savings / max(baseline_cost, 1) * 100)}%).\n\n"
            f"**3. Provider strengths:** {'; '.join((rec_model_data.get('strengths', []) if rec_model_data else []))}\n\n"
            f"**4. Best suited for:** {', '.join((rec_model_data.get('best_for', []) if rec_model_data else []))}\n\n"
            f"**Full rationale:** {rationale[:400]}{'...' if len(rationale) > 400 else ''}"
        )
        return ChatResponse(text=text, chart=None)

    # ── 7. Compare all models ───────────────────────────────────────────────
    if any(w in msg for w in ["compare", "all model", "list", "options", "alternatives", "other model"]):
        classification = use_case.triage_classification or "Moderate"
        if classification == "Simple":
            input_t, output_t, daily_r = 200, 100, 10_000
        elif classification == "Complex":
            input_t, output_t, daily_r = 1000, 500, 5_000
        else:
            input_t, output_t, daily_r = 500, 300, 10_000

        model_costs = []
        for m in ALL_MODELS:
            cost = _calc_monthly_cost(m, daily_r, input_t, output_t)
            model_costs.append((m, cost))
        model_costs.sort(key=lambda x: x[1])

        text = f"### All Available Models — Ranked by Cost\n*Estimated at {input_t} input + {output_t} output tokens, {daily_r:,} req/day*\n\n"
        text += "| Model | Provider | Tier | Est. Monthly Cost |\n|---|---|---|---|\n"
        for m, cost in model_costs:
            marker = " ✅" if m["name"] == rec_model_name else ""
            text += f"| **{m['name']}{marker}** | {m['provider']} | {m['tier']} | ${cost:,.2f} |\n"

        chart_data = _build_cost_chart(
            [(m["name"], cost) for m, cost in model_costs[:10]],
            f"All Models — Monthly Cost at {daily_r:,} req/day"
        )
        return ChatResponse(text=text, chart=chart_data)

    # ── 8. Latency questions ─────────────────────────────────────────────────
    if any(w in msg for w in ["latency", "speed", "fast", "slow", "response time", "real-time", "realtime"]):
        fast_models = [m for m in ALL_MODELS if m["tier"] == "Small"]
        text = (
            f"### ⚡ Latency Guide\n\n"
            f"**Fastest models (Small tier):**\n"
            + "\n".join([f"- **{m['name']}** ({m['provider']}): {'; '.join(m['strengths'][:2])}" for m in fast_models[:5]])
            + f"\n\n**Your recommendation ({rec_model_name}):** "
            f"{'Optimized for speed — ideal for real-time applications.' if _find_model_by_name(rec_model_name) and _find_model_by_name(rec_model_name).get('tier') == 'Small' else 'Balanced latency. If sub-500ms is critical, consider Amazon Nova Micro or Gemini Flash.'}\n\n"
            f"**Rules of thumb:**\n"
            f"- Real-time chat (<1s): Use Small tier (Nova Micro, Gemini Flash, GPT-4o Mini)\n"
            f"- Batch processing (>5s ok): Any tier works\n"
            f"- Reasoning models (o1, DeepSeek-R1): Add 5-30s for thinking chains"
        )
        return ChatResponse(text=text, chart=None)

    # ── 8b. Development / Setup steps questions ────────────────────────────────
    dev_keywords = ["step", "develop", "phase", "guide", "setup", "implement", "deploy", "build", "how to start", "start with"]
    if any(w in msg for w in dev_keywords):
        dev_guide = recommendation.development_guide or []
        if dev_guide:
            text = f"### 🛠️ Development & Deployment Steps for **{rec_model_name}** on **{rec_cloud}**\n\n"
            for phase_dict in dev_guide:
                if not isinstance(phase_dict, dict):
                    continue
                phase_num = phase_dict.get("phase", 1)
                phase_name = phase_dict.get("phase_name", "")
                duration = phase_dict.get("duration", "")
                text += f"#### Phase {phase_num}: {phase_name} *({duration})*\n"
                for step_dict in phase_dict.get("steps", []):
                    if not isinstance(step_dict, dict):
                        continue
                    step_name = step_dict.get("step", "")
                    detail = step_dict.get("detail", "")
                    text += f"- **{step_name}**: {detail}\n"
                    resources = step_dict.get("resources", [])
                    if resources:
                        text += "  *Resources:* " + ", ".join([f"[Link]({r})" for r in resources]) + "\n"
                text += "\n"
            return ChatResponse(text=text, chart=None)
        else:
            text = (
                f"### 🛠️ Development & Setup Steps\n\n"
                f"Your recommendation for **{rec_model_name}** on **{rec_cloud}** can be set up in these main steps:\n"
                f"1. **Cloud Setup**: Configure your {rec_cloud} account in region `{rec_region}`.\n"
                f"2. **API Access**: Enable model access for {rec_model_name}.\n"
                f"3. **Backend Service**: Deploy a compute instance (e.g. Lambda/Cloud Run) to handle prompt logic.\n"
                f"4. **Database & Storage**: Setup session history storage.\n"
                f"5. **Client Integration**: Connect your frontend app to the API endpoints."
            )
            return ChatResponse(text=text, chart=None)

    # ── 9. Default / general questions ──────────────────────────────────────
    rec_model_data = _find_model_by_name(rec_model_name)
    text = (
        f"### AI Advisor — Your Recommendation Summary\n\n"
        f"**Recommended:** {rec_model_name} on {rec_cloud} · {rec_region}\n"
        f"**Monthly cost:** ${rec_cost:,.2f} (saves ${savings:,.2f} vs baseline)\n\n"
        f"**I can answer questions like:**\n"
        f'- 💰 *\"If I send 500 input + 200 output tokens per request, what\'s my cost?\"*\n'
        f'- 📊 *\"Compare GPT-4o vs Gemini 1.5 Pro for my use case\"*\n'
        f'- 💼 *\"What models fit within $200/month?\"*\n'
        f'- 🔒 *\"Does this deployment meet GDPR requirements?\"*\n'
        f'- ⚡ *\"Which model has the lowest latency?\"*\n'
        f'- 🤔 *\"Would Amazon Nova Pro work for this?\"*\n'
        f'- 📋 *\"Show me all available models ranked by cost\"*\n\n'
        f"Just ask — I have full pricing data for all {len(ALL_MODELS)} models in my knowledge base."
    )
    return ChatResponse(text=text, chart=None)

@router.post("/chat", response_model=ChatResponse)
async def chat_follow_up(
    payload: ChatPayload,
    db: Session = Depends(get_db),
):
    use_case = None
    recommendation = None
    try:
        use_case = db.query(UseCase).filter(UseCase.id == payload.use_case_id).first()
        if not use_case:
            raise HTTPException(status_code=404, detail="Use case not found")

        recommendation = db.query(Recommendation).filter(Recommendation.use_case_id == payload.use_case_id).first()
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        # Build model KB summary for Gemini prompt
        _lazy_load_kb()
        model_kb_lines = []
        for m in ALL_MODELS:
            model_kb_lines.append(
                f"- {m['name']} ({m['provider']}, {m['tier']}): "
                f"${m['cost_per_1k_input_tokens']}/1K in, ${m['cost_per_1k_output_tokens']}/1K out, "
                f"ctx={m['max_context']:,}, best_for={', '.join(m.get('best_for', []))}"
            )

        # Build cloud services summary
        cloud_svcs = recommendation.cloud_services or []
        cloud_svcs_summary = ", ".join([s.get("service_name","") for s in cloud_svcs[:6] if isinstance(s, dict)]) or "N/A"

        # Build dev guide summary
        dev_guide = recommendation.development_guide or []
        dev_guide_summary = " → ".join([p.get("phase_name","") for p in dev_guide[:5] if isinstance(p, dict)]) or "N/A"

        # Build compliance summary
        flags = recommendation.compliance_flags or []
        compliance_summary = "; ".join([f"{f.get('flag','')}: {f.get('status','')}" for f in flags[:4] if isinstance(f, dict)]) or "N/A"

        # Build alternatives summary
        alts = recommendation.alternatives or []
        alts_summary = "; ".join([f"{a.get('model','')} on {a.get('cloud','')} (${a.get('estimated_monthly_cost',0):.0f}/mo)" for a in alts[:3] if isinstance(a, dict)]) or "N/A"

        # Compute savings
        estimated_savings = round((recommendation.baseline_cost or 0) - (recommendation.estimated_monthly_cost or 0), 2)

        system_instruction = CHAT_SYSTEM_PROMPT.format(
            description=use_case.description,
            extracted_fields=json.dumps(use_case.extracted_fields),
            triage_classification=use_case.triage_classification or "Moderate",
            triage_reasoning=use_case.triage_reasoning or "N/A",
            recommended_model=recommendation.recommended_model,
            model_provider=recommendation.model_provider or "",
            recommended_cloud=recommendation.recommended_cloud,
            region=recommendation.recommended_region or recommendation.region or "",
            estimated_monthly_cost=recommendation.estimated_monthly_cost,
            baseline_cost=recommendation.baseline_cost,
            estimated_savings=estimated_savings,
            model_rationale=recommendation.model_rationale or recommendation.rationale or "",
            model_strengths=", ".join(recommendation.model_strengths or []),
            cloud_services=cloud_svcs_summary,
            dev_guide_phases=dev_guide_summary,
            architecture_summary=(recommendation.architecture_summary or "")[:300],
            compliance_summary=compliance_summary,
            alternatives_summary=alts_summary,
            confidence_score=recommendation.confidence_score or 0,
            alternatives=json.dumps(recommendation.alternatives),
            model_kb="\n".join(model_kb_lines),
        )

        settings = get_settings()
        api_key = settings.GEMINI_API_KEY

        if not api_key or "gemini-key" in api_key or "your-key" in api_key:
            logger.warning("Gemini API key not configured. Using local chat engine.")
            return _get_local_chat_response(recommendation, use_case, payload.messages[-1].content, payload.messages)

        contents = []
        for msg in payload.messages:
            contents.append({
                "role": "user" if msg.role == "user" else "model",
                "parts": [{"text": msg.content}]
            })

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        gemini_payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {"responseMimeType": "application/json"}
        }

        import asyncio
        gemini_response = None
        max_retries = 3
        backoff = 1.0

        async with httpx.AsyncClient() as client:
            for attempt in range(max_retries):
                try:
                    response = await client.post(url, json=gemini_payload, timeout=20.0)
                    if response.status_code == 200:
                        gemini_response = response.json()
                        break
                    elif response.status_code in (429, 503):
                        logger.warning(
                            "Gemini API returned %s during chat. Attempt %s/%s. Retrying in %ss...",
                            response.status_code, attempt + 1, max_retries, backoff
                        )
                        await asyncio.sleep(backoff)
                        backoff *= 2.0
                    else:
                        logger.warning("Gemini API returned status %s during chat.", response.status_code)
                        break
                except Exception as e:
                    logger.warning("Exception during chat API call: %s. Retrying...", e)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= 2.0

        if gemini_response:
            try:
                raw_text = gemini_response["candidates"][0]["content"]["parts"][0]["text"].strip()
                chat_data = json.loads(raw_text)
                return ChatResponse(
                    text=chat_data.get("text", "I'm sorry, I couldn't process that question."),
                    chart=chat_data.get("chart"),
                    suggested_model=chat_data.get("suggested_model"),
                    suggested_cloud=chat_data.get("suggested_cloud")
                )
            except Exception as e:
                logger.warning("Failed to parse Gemini chat response JSON: %s. Using local engine.", e)

        # Fallback to local engine
        logger.warning("Gemini API unavailable or failed. Using local chat engine.")
        return _get_local_chat_response(recommendation, use_case, payload.messages[-1].content, payload.messages)

    except json.JSONDecodeError as e:
        logger.warning("Failed to parse Gemini chat response JSON: %s. Using local engine.", e)
        if recommendation and use_case:
            return _get_local_chat_response(recommendation, use_case, payload.messages[-1].content, payload.messages)
        raise HTTPException(status_code=500, detail="Invalid chatbot response")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during chat processing, applying local engine")
        if recommendation and use_case:
            return _get_local_chat_response(recommendation, use_case, payload.messages[-1].content, payload.messages)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
