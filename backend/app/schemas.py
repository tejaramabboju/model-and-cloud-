"""
Pydantic schemas for request/response validation and serialization.
Updated for v3: 20-field extraction, 8-section guidebook, clarification round-trip.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ─── Input Schemas ───────────────────────────────────────────────────────────

class StructuredFormFields(BaseModel):
    """Optional structured fields from the form (all optional — form fields override LLM extraction)."""
    project_name: Optional[str] = None
    daily_requests: Optional[str] = None          # "unknown" | "500" | "5000" | "50000" | "500000"
    avg_input_tokens: Optional[str] = None        # "unknown" | "100" | "500" | "2500" | "7500"
    avg_output_tokens: Optional[str] = None       # "unknown" | "50" | "250" | "750"
    monthly_budget_usd: Optional[float] = None
    number_of_users: Optional[int] = None
    data_sensitivity: Optional[str] = None        # none|low|medium|high|critical
    compliance_region: Optional[str] = None       # EU|USA|India|UK|Australia|Canada|global|none
    compliance_standards: Optional[list[str]] = None  # ["GDPR","HIPAA",...]
    existing_cloud: Optional[str] = None          # AWS|GCP|Azure|none
    team_expertise: Optional[str] = None          # beginner|intermediate|expert
    streaming_needed: Optional[bool] = None
    fine_tuning_needed: Optional[bool] = None
    on_premise_required: Optional[bool] = None
    multimodal_needs: Optional[bool] = None
    high_availability: Optional[bool] = None


class UseCaseSubmit(BaseModel):
    """Schema for submitting a new use case — description + optional structured fields."""
    description: str = Field(
        ...,
        min_length=5,
        max_length=5000,
        description="Description of the AI use case",
    )
    structured_fields: Optional[StructuredFormFields] = None


class ClarificationSubmit(BaseModel):
    """User's answers to clarification questions."""
    answers: dict[str, str] = Field(default_factory=dict)


class RecommendationSwitchSubmit(BaseModel):
    """Schema for requesting a switch of the recommended model and/or cloud provider."""
    recommended_model: Optional[str] = None
    recommended_cloud: Optional[str] = None


class FeedbackSubmit(BaseModel):
    """Schema for submitting feedback on a recommendation."""
    recommendation_id: int
    rating: bool  # True = thumbs up, False = thumbs down
    comment: Optional[str] = None


# ─── Extracted / Intermediate Schemas ────────────────────────────────────────

class ExtractedFields(BaseModel):
    """All 20 fields extracted from the use case description + form."""
    project_name: str = "unknown"
    task_type: str = "unknown"
    industry: str = "unknown"
    data_sensitivity: str = "none"
    compliance_region: str = "unknown"
    compliance_standards: list[str] = []
    daily_requests: str = "unknown"
    avg_input_tokens: str = "unknown"
    avg_output_tokens: str = "unknown"
    monthly_budget_usd: Optional[float] = None
    latency_requirement: str = "unknown"
    existing_cloud: str = "none"
    existing_services: list[str] = []
    team_expertise: str = "unknown"
    multimodal_needs: Optional[bool] = None
    streaming_needed: Optional[bool] = None
    fine_tuning_needed: Optional[bool] = None
    on_premise_required: Optional[bool] = None
    high_availability: Optional[bool] = None
    number_of_users: Optional[int] = None
    description_summary: str = ""

    # Legacy fields (kept for backwards compat with DB/chat)
    scale_volume: str = "unknown"
    latency_need: str = "unknown"
    budget_hint: str = "unknown"

    model_config = {"extra": "allow"}


class TriageResult(BaseModel):
    """Triage classification with optional clarification questions."""
    classification: str = Field(..., description="Simple, Moderate, or Complex")
    reasoning: str = ""
    needs_clarification: bool = False
    clarification_questions: list[str] = []


# ─── Guidebook Section Schemas ────────────────────────────────────────────────

class CloudService(BaseModel):
    """A specific cloud service recommended for this architecture."""
    service_name: str
    purpose: str
    why_needed: str
    setup_complexity: str = "Medium"  # Easy | Medium | Advanced


class CostBreakdownItem(BaseModel):
    """Line item in the cost breakdown table."""
    item: str
    monthly_usd: float


class CostBreakdown(BaseModel):
    """Full cost breakdown with LLM + infra costs."""
    llm_cost_monthly: float = 0.0
    llm_cost_per_1k_requests: float = 0.0
    llm_cost_per_user: Optional[float] = None
    cloud_infra_cost_monthly: float = 0.0
    total_estimated_monthly: float = 0.0
    baseline_comparison: float = 0.0
    estimated_savings: float = 0.0
    assumptions: list[str] = []
    cost_breakdown_items: list[CostBreakdownItem] = []


class DevStep(BaseModel):
    """A single step within a development phase."""
    step: str
    detail: str
    resources: list[str] = []


class DevPhase(BaseModel):
    """A development phase with multiple steps."""
    phase: int
    phase_name: str
    duration: str
    steps: list[DevStep] = []


class ComplianceFlag(BaseModel):
    """A single compliance check result."""
    flag: str
    status: str = Field(..., description="pass, fail, or warning")
    detail: str
    note: Optional[str] = None

    model_config = {"extra": "allow"}


class Alternative(BaseModel):
    """An alternative recommendation option."""
    model: str
    cloud: str
    region: str
    estimated_monthly_cost: float
    trade_off: str
    best_for: str = ""

    model_config = {"extra": "allow"}


# ─── Response Schemas ────────────────────────────────────────────────────────

class RecommendationResponse(BaseModel):
    """Full 8-section guidebook recommendation response."""
    id: int
    use_case_id: int

    # Section 1 — Model
    recommended_model: str
    model_provider: str = ""
    model_rationale: str = ""
    model_strengths: list[str] = []
    model_limitations: list[str] = []

    # Section 2 — Cloud
    recommended_cloud: str
    recommended_region: str = ""
    region: str = ""  # legacy alias
    cloud_rationale: str = ""
    cloud_services: list[CloudService] = []

    # Section 3 — Cost
    cost_breakdown: Optional[CostBreakdown] = None
    within_budget: Optional[bool] = None
    estimated_monthly_cost: float = 0.0
    baseline_cost: float = 0.0

    # Section 4 — Dev Guide
    development_guide: list[DevPhase] = []

    # Section 5 — Architecture
    architecture_summary: str = ""
    architecture_components: list[str] = []
    data_flow: list[str] = []

    # Section 6 — Compliance
    compliance_flags: list[ComplianceFlag] = []
    security_recommendations: list[str] = []

    # Section 7 — Alternatives
    alternatives: list[Alternative] = []

    # Section 8 — Metadata
    confidence_score: int = 0
    confidence_reasoning: str = ""
    missing_info_impact: str = "none"

    # Legacy rationale field
    rationale: str = ""

    created_at: datetime

    model_config = {"from_attributes": True}


class ClarificationResponse(BaseModel):
    """Returned when triage needs more info before generating a full recommendation."""
    id: int
    status: str = "needs_clarification"
    clarification_message: str
    clarification_questions: list[str] = []


class FeedbackResponse(BaseModel):
    """Feedback response."""
    id: int
    recommendation_id: int
    rating: bool
    comment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UseCaseResponse(BaseModel):
    """Full use case response with embedded recommendation."""
    id: int
    status: str = "complete"
    description: str
    extracted_fields: Optional[ExtractedFields] = None
    triage: Optional[TriageResult] = None
    recommendation: Optional[RecommendationResponse] = None
    created_at: datetime
    clarification_message: Optional[str] = None
    clarification_questions: list[str] = []

    model_config = {"from_attributes": True}


# ─── Dashboard Schemas ───────────────────────────────────────────────────────

class ModelDistribution(BaseModel):
    model: str
    count: int


class CloudDistribution(BaseModel):
    cloud: str
    count: int


class DashboardStats(BaseModel):
    total_use_cases: int = 0
    total_monthly_spend: float = 0.0
    total_savings: float = 0.0
    avg_confidence: float = 0.0
    recommendation_accuracy: Optional[float] = None
    model_distribution: list[ModelDistribution] = []
    cloud_distribution: list[CloudDistribution] = []
