"""
Use Cases router — v3 with clarification round-trip and 8-section guidebook.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload, Session

from app.database import get_db
from app.models import UseCase, Recommendation
from app.schemas import (
    UseCaseSubmit,
    UseCaseResponse,
    ClarificationSubmit,
    ClarificationResponse,
    RecommendationSwitchSubmit,
    ExtractedFields,
    TriageResult,
    RecommendationResponse,
    ComplianceFlag,
    Alternative,
    CloudService,
    CostBreakdown,
    CostBreakdownItem,
    DevPhase,
    DevStep,
)
from app.services.extractor import extract_fields
from app.services.triage import classify_complexity
from app.services.clarifier import generate_clarification_message
from app.services.knowledge_base import (
    get_all_models,
    get_models_by_tier,
    get_all_cloud_providers,
    get_compliant_clouds,
    format_models_for_llm,
    format_clouds_for_llm,
)
from app.services.recommender import generate_recommendation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["use-cases"])


# ─── Helper: build ExtractedFields safely from dict ──────────────────────────

def _build_extracted_fields(extracted: dict) -> ExtractedFields:
    """Build an ExtractedFields model safely, ignoring unknown keys."""
    valid_fields = ExtractedFields.model_fields.keys()
    safe = {k: v for k, v in extracted.items() if k in valid_fields}
    return ExtractedFields(**safe)


def _build_recommendation_response(rec: Recommendation, use_case_id: int) -> RecommendationResponse:
    """Build a RecommendationResponse from a DB Recommendation model."""

    # Build cloud_services
    cloud_services_raw = rec.cloud_services or []
    cloud_services = [CloudService(**cs) for cs in cloud_services_raw if isinstance(cs, dict)]

    # Build cost_breakdown
    cost_breakdown = None
    if rec.cost_breakdown and isinstance(rec.cost_breakdown, dict):
        cb = rec.cost_breakdown
        items = [CostBreakdownItem(**it) for it in cb.get("cost_breakdown_items", []) if isinstance(it, dict)]
        cost_breakdown = CostBreakdown(
            llm_cost_monthly=cb.get("llm_cost_monthly", 0.0),
            llm_cost_per_1k_requests=cb.get("llm_cost_per_1k_requests", 0.0),
            llm_cost_per_user=cb.get("llm_cost_per_user"),
            cloud_infra_cost_monthly=cb.get("cloud_infra_cost_monthly", 0.0),
            total_estimated_monthly=cb.get("total_estimated_monthly", 0.0),
            baseline_comparison=cb.get("baseline_comparison", 0.0),
            estimated_savings=cb.get("estimated_savings", 0.0),
            assumptions=cb.get("assumptions", []),
            cost_breakdown_items=items,
        )

    # Build development_guide
    dev_guide_raw = rec.development_guide or []
    dev_guide = []
    for phase_dict in dev_guide_raw:
        if not isinstance(phase_dict, dict):
            continue
        steps = [DevStep(**s) for s in phase_dict.get("steps", []) if isinstance(s, dict)]
        dev_guide.append(DevPhase(
            phase=phase_dict.get("phase", 1),
            phase_name=phase_dict.get("phase_name", ""),
            duration=phase_dict.get("duration", ""),
            steps=steps,
        ))

    # Build compliance_flags
    compliance_flags = []
    for f in (rec.compliance_flags or []):
        if isinstance(f, dict):
            compliance_flags.append(ComplianceFlag(
                flag=f.get("flag", f.get("check", "")),
                status=f.get("status", "pass"),
                detail=f.get("detail", f.get("note", "")),
                note=f.get("note"),
            ))

    # Build alternatives
    alternatives = []
    for a in (rec.alternatives or []):
        if isinstance(a, dict):
            alternatives.append(Alternative(
                model=a.get("model", ""),
                cloud=a.get("cloud", ""),
                region=a.get("region", ""),
                estimated_monthly_cost=float(a.get("estimated_monthly_cost", 0)),
                trade_off=a.get("trade_off", ""),
                best_for=a.get("best_for", ""),
            ))

    region = rec.recommended_region or rec.region or ""

    return RecommendationResponse(
        id=rec.id,
        use_case_id=use_case_id,
        recommended_model=rec.recommended_model,
        model_provider=rec.model_provider or "",
        model_rationale=rec.model_rationale or "",
        model_strengths=rec.model_strengths or [],
        model_limitations=rec.model_limitations or [],
        recommended_cloud=rec.recommended_cloud,
        recommended_region=region,
        region=region,
        cloud_rationale=rec.cloud_rationale or "",
        cloud_services=cloud_services,
        cost_breakdown=cost_breakdown,
        within_budget=rec.within_budget,
        estimated_monthly_cost=rec.estimated_monthly_cost or 0.0,
        baseline_cost=rec.baseline_cost or 0.0,
        development_guide=dev_guide,
        architecture_summary=rec.architecture_summary or "",
        architecture_components=rec.architecture_components or [],
        data_flow=rec.data_flow or [],
        compliance_flags=compliance_flags,
        security_recommendations=rec.security_recommendations or [],
        alternatives=alternatives,
        confidence_score=rec.confidence_score or 0,
        confidence_reasoning=rec.confidence_reasoning or "",
        missing_info_impact=rec.missing_info_impact or "none",
        rationale=rec.rationale or rec.model_rationale or "",
        created_at=rec.created_at,
    )


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/use-case")
async def submit_use_case(
    payload: UseCaseSubmit,
    db: Session = Depends(get_db),
):
    """
    Submit a use case and receive either:
    - A full 8-section guidebook recommendation (status: complete)
    - A clarification request (status: needs_clarification)

    Pipeline:
    1. Extract 20 structured fields (merge form values)
    2. Triage: classify complexity + detect missing critical info
    3a. If needs_clarification: store partial UseCase, return clarification
    3b. Else: run full recommendation pipeline
    4. Return UseCaseResponse or ClarificationResponse
    """
    try:
        description = payload.description.strip()
        form_fields = payload.structured_fields.model_dump() if payload.structured_fields else None

        # ── Step 1: Extract fields ───────────────────────────────────────────
        extracted = await extract_fields(description, form_fields)
        logger.info("Extracted fields: %s", extracted)

        # ── Step 2: Triage classification ────────────────────────────────────
        triage = await classify_complexity(description, extracted)
        logger.info("Triage: %s", triage)

        # ── Step 3a: Clarification check ──────────────────────────────────────
        if triage.get("needs_clarification") and triage.get("clarification_questions"):
            clarification_message = await generate_clarification_message(
                triage["clarification_questions"]
            )

            # Store a partial use case
            use_case = UseCase(
                description=description,
                extracted_fields=extracted,
                triage_classification=triage.get("classification"),
                triage_reasoning=triage.get("reasoning"),
                status="needs_clarification",
                triage_needs_clarification=True,
                triage_clarification_questions=triage.get("clarification_questions", []),
                created_at=datetime.now(timezone.utc),
            )
            db.add(use_case)
            db.commit()
            db.refresh(use_case)

            logger.info("Clarification needed for use case id %s", use_case.id)
            return {
                "id": use_case.id,
                "status": "needs_clarification",
                "clarification_message": clarification_message,
                "clarification_questions": triage.get("clarification_questions", []),
            }

        # ── Step 3b: Full recommendation pipeline ─────────────────────────────
        return await _run_recommendation_pipeline(description, extracted, triage, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing use case submission")
        raise HTTPException(status_code=500, detail=f"Failed to process use case: {str(e)}")


@router.post("/use-case/{use_case_id}/clarify")
async def submit_clarification(
    use_case_id: int,
    payload: ClarificationSubmit,
    db: Session = Depends(get_db),
):
    """
    Accept user's clarification answers and generate the full recommendation.
    """
    try:
        use_case = db.get(UseCase, use_case_id)
        if not use_case:
            raise HTTPException(status_code=404, detail="Use case not found")

        # Merge clarification answers into extracted fields
        extracted = dict(use_case.extracted_fields or {})
        answers = payload.answers or {}

        # Map common answer patterns to field values
        for key, val in answers.items():
            if not val or val.strip().lower() in ("skip", "i don't know", "not sure", ""):
                continue
            val = val.strip()
            # Map daily_requests answers
            if "request" in key.lower() or "daily" in key.lower():
                if "1,000" in val or "1k" in val.lower() or "under" in val.lower():
                    extracted["daily_requests"] = "500"
                    extracted["scale_volume"] = "low (<1K/day)"
                elif "10,000" in val or "10k" in val.lower():
                    extracted["daily_requests"] = "5000"
                    extracted["scale_volume"] = "medium (1K-100K/day)"
                elif "100,000" in val or "100k" in val.lower():
                    extracted["daily_requests"] = "50000"
                    extracted["scale_volume"] = "high (>100K/day)"
                elif "100k+" in val.lower() or "over 100" in val.lower():
                    extracted["daily_requests"] = "500000"
                    extracted["scale_volume"] = "high (>100K/day)"
            # Budget answers
            elif "budget" in key.lower() or "$" in val:
                import re
                nums = re.findall(r"\d+", val.replace(",", ""))
                if nums:
                    extracted["monthly_budget_usd"] = float(nums[0])
                    extracted["budget_hint"] = f"~${nums[0]}/month"
            # Region answers
            elif "region" in key.lower() or "country" in key.lower():
                val_lower = val.lower()
                if "eu" in val_lower or "europe" in val_lower:
                    extracted["compliance_region"] = "EU"
                elif "usa" in val_lower or "us" in val_lower or "united states" in val_lower:
                    extracted["compliance_region"] = "USA"
                elif "india" in val_lower:
                    extracted["compliance_region"] = "India"
                elif "uk" in val_lower or "united kingdom" in val_lower:
                    extracted["compliance_region"] = "UK"
            # Sensitivity answers
            elif "health" in val.lower() or "phi" in val.lower():
                extracted["data_sensitivity"] = "critical"
                extracted["compliance_standards"] = extracted.get("compliance_standards", []) + ["HIPAA"]
            elif "financial" in val.lower():
                extracted["data_sensitivity"] = "high"
            # Token/doc size answers
            elif "page" in val.lower() or "document" in val.lower():
                if "short" in val.lower() or "<200" in val:
                    extracted["avg_input_tokens"] = "200"
                elif "1-5" in val or "medium" in val.lower():
                    extracted["avg_input_tokens"] = "1500"
                elif "5-20" in val or "long" in val.lower():
                    extracted["avg_input_tokens"] = "5000"
                elif "20+" in val or "very long" in val.lower():
                    extracted["avg_input_tokens"] = "15000"

        # Update the use case record
        use_case.extracted_fields = extracted
        use_case.clarification_answers = answers
        use_case.status = "complete"
        db.commit()

        # Re-run triage with updated fields (no more clarification questions)
        description = use_case.description
        triage = {
            "classification": use_case.triage_classification or "Moderate",
            "reasoning": use_case.triage_reasoning or "",
            "needs_clarification": False,
            "clarification_questions": [],
        }

        return await _run_recommendation_pipeline(description, extracted, triage, db, existing_use_case=use_case)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing clarification")
        raise HTTPException(status_code=500, detail=f"Failed to process clarification: {str(e)}")


@router.post("/use-case/{use_case_id}/switch", response_model=UseCaseResponse)
async def switch_recommendation(
    use_case_id: int,
    payload: RecommendationSwitchSubmit,
    db: Session = Depends(get_db),
):
    """
    Switch the recommended model and/or cloud provider, and regenerate the entire guidebook.
    """
    try:
        use_case = db.get(UseCase, use_case_id)
        if not use_case:
            raise HTTPException(status_code=404, detail="Use case not found")

        description = use_case.description
        extracted = dict(use_case.extracted_fields or {})

        triage = {
            "classification": use_case.triage_classification or "Moderate",
            "reasoning": use_case.triage_reasoning or "",
            "needs_clarification": False,
            "clarification_questions": [],
        }

        if payload.recommended_cloud:
            extracted["existing_cloud"] = payload.recommended_cloud

        use_case.extracted_fields = extracted
        db.commit()

        return await _run_recommendation_pipeline(
            description,
            extracted,
            triage,
            db,
            existing_use_case=use_case,
            forced_model=payload.recommended_model,
            forced_cloud=payload.recommended_cloud
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing recommendation switch")
        raise HTTPException(status_code=500, detail=f"Failed to switch recommendation: {str(e)}")


async def _run_recommendation_pipeline(
    description: str,
    extracted: dict,
    triage: dict,
    db: Session,
    existing_use_case: UseCase | None = None,
    forced_model: str | None = None,
    forced_cloud: str | None = None,
) -> UseCaseResponse:
    """Run the full recommendation pipeline and store results."""
    classification = triage.get("classification", "Moderate")

    # KB query
    if classification == "Simple":
        relevant_models = get_models_by_tier("Small") + get_models_by_tier("Medium")
    elif classification == "Complex":
        relevant_models = get_models_by_tier("Large") + get_models_by_tier("Medium")
    else:
        relevant_models = get_all_models()

    data_sensitivity = extracted.get("data_sensitivity", "none").lower()
    compliance_region = extracted.get("compliance_region", "unknown").lower()

    required_certs = []
    if data_sensitivity in ("high", "critical"):
        required_certs.extend(["HIPAA", "GDPR"])
    elif data_sensitivity == "medium":
        required_certs.append("GDPR")
    if compliance_region in ("eu", "europe"):
        if "GDPR" not in required_certs:
            required_certs.append("GDPR")

    region_kw = None
    if compliance_region in ("eu", "europe"):
        region_kw = "EU"
    elif compliance_region in ("india", "in"):
        region_kw = "India"
    elif compliance_region in ("us", "usa", "united states"):
        region_kw = "USA"

    compliant_clouds = (
        get_compliant_clouds(required_certs, region_kw) if required_certs else get_all_cloud_providers()
    )
    kb_context = format_models_for_llm(relevant_models) + "\n" + format_clouds_for_llm(compliant_clouds)
    compliant_options = _build_compliant_options(relevant_models, compliant_clouds)

    # Generate recommendation
    rec_data = await generate_recommendation(
        description=description,
        extracted_fields=extracted,
        triage=triage,
        kb_context=kb_context,
        compliant_options=compliant_options,
        forced_model=forced_model,
        forced_cloud=forced_cloud,
    )
    logger.info("Recommendation: %s on %s (confidence: %s)", rec_data.get("recommended_model"), rec_data.get("recommended_cloud"), rec_data.get("confidence_score"))

    # Store in DB
    if existing_use_case:
        use_case = existing_use_case
        if use_case.recommendation:
            db.delete(use_case.recommendation)
            db.flush()
    else:
        use_case = UseCase(
            description=description,
            extracted_fields=extracted,
            triage_classification=triage.get("classification"),
            triage_reasoning=triage.get("reasoning"),
            status="complete",
            triage_needs_clarification=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(use_case)
        db.flush()

    recommendation = Recommendation(
        use_case_id=use_case.id,
        recommended_model=rec_data.get("recommended_model", "Unknown"),
        model_provider=rec_data.get("model_provider", ""),
        model_rationale=rec_data.get("model_rationale", ""),
        model_strengths=rec_data.get("model_strengths", []),
        model_limitations=rec_data.get("model_limitations", []),
        recommended_cloud=rec_data.get("recommended_cloud", "Unknown"),
        recommended_region=rec_data.get("recommended_region", rec_data.get("region", "")),
        region=rec_data.get("region", rec_data.get("recommended_region", "")),
        cloud_rationale=rec_data.get("cloud_rationale", ""),
        cloud_services=rec_data.get("cloud_services", []),
        estimated_monthly_cost=float(rec_data.get("estimated_monthly_cost", 0)),
        baseline_cost=float(rec_data.get("baseline_cost", 0)),
        cost_breakdown=rec_data.get("cost_breakdown"),
        within_budget=rec_data.get("within_budget"),
        development_guide=rec_data.get("development_guide", []),
        architecture_summary=rec_data.get("architecture_summary", ""),
        architecture_components=rec_data.get("architecture_components", []),
        data_flow=rec_data.get("data_flow", []),
        compliance_flags=rec_data.get("compliance_flags", []),
        security_recommendations=rec_data.get("security_recommendations", []),
        alternatives=rec_data.get("alternatives", []),
        confidence_score=rec_data.get("confidence_score", 0),
        confidence_reasoning=rec_data.get("confidence_reasoning", ""),
        missing_info_impact=rec_data.get("missing_info_impact", "none"),
        rationale=rec_data.get("rationale", rec_data.get("model_rationale", "")),
        created_at=datetime.now(timezone.utc),
    )
    db.add(recommendation)
    db.commit()
    db.refresh(use_case)
    db.refresh(recommendation)

    return UseCaseResponse(
        id=use_case.id,
        status="complete",
        description=use_case.description,
        extracted_fields=_build_extracted_fields(extracted),
        triage=TriageResult(
            classification=triage.get("classification", "Moderate"),
            reasoning=triage.get("reasoning", ""),
            needs_clarification=False,
            clarification_questions=[],
        ),
        recommendation=_build_recommendation_response(recommendation, use_case.id),
        created_at=use_case.created_at,
    )


@router.get("/use-cases", response_model=list[UseCaseResponse])
async def list_use_cases(db: Session = Depends(get_db)):
    """Return all use cases with their recommendations, ordered by most recent first."""
    try:
        stmt = (
            select(UseCase)
            .options(selectinload(UseCase.recommendation).selectinload(Recommendation.feedback))
            .order_by(UseCase.created_at.desc())
        )
        result = db.execute(stmt)
        use_cases = result.scalars().all()

        responses = []
        for uc in use_cases:
            rec_response = None
            if uc.recommendation:
                rec_response = _build_recommendation_response(uc.recommendation, uc.id)

            triage = None
            if uc.triage_classification:
                triage = TriageResult(
                    classification=uc.triage_classification,
                    reasoning=uc.triage_reasoning or "",
                    needs_clarification=uc.triage_needs_clarification or False,
                    clarification_questions=uc.triage_clarification_questions or [],
                )

            extracted = None
            if uc.extracted_fields:
                extracted = _build_extracted_fields(uc.extracted_fields)

            responses.append(UseCaseResponse(
                id=uc.id,
                status=uc.status or "complete",
                description=uc.description,
                extracted_fields=extracted,
                triage=triage,
                recommendation=rec_response,
                created_at=uc.created_at,
            ))

        return responses

    except Exception as e:
        logger.exception("Error listing use cases")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve use cases: {str(e)}")


def _build_compliant_options(models: list[dict], clouds: list[dict]) -> list[dict]:
    """Build all valid model × cloud × region combinations."""
    options = []
    for cloud in clouds:
        supported = {m.lower() for m in cloud.get("supported_models", [])}
        for model in models:
            if model["name"].lower() in supported:
                for region in cloud.get("regions", []):
                    options.append({
                        "model": model["name"],
                        "cloud": cloud["name"],
                        "region": region,
                        "model_data": model,
                        "cloud_data": cloud,
                    })
    return options
