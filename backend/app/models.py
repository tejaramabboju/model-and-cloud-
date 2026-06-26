"""
SQLAlchemy ORM models for the AI Model & Cloud Advisor.
v3: added clarification columns + extended guidebook columns on Recommendation.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


class UseCase(Base):
    """Stores submitted use cases with extracted fields and triage info."""

    __tablename__ = "use_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text, nullable=False)
    extracted_fields = Column(JSON, nullable=True)          # 20-field dict
    triage_classification = Column(String(50), nullable=True)
    triage_reasoning = Column(Text, nullable=True)
    # v3: clarification support
    status = Column(String(30), default="complete")          # "complete" | "needs_clarification"
    triage_needs_clarification = Column(Boolean, default=False)
    triage_clarification_questions = Column(JSON, nullable=True)  # list of question strings
    clarification_answers = Column(JSON, nullable=True)           # dict field->answer
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    recommendation = relationship(
        "Recommendation",
        back_populates="use_case",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<UseCase(id={self.id}, classification={self.triage_classification}, status={self.status})>"


class Recommendation(Base):
    """Stores AI-generated recommendations for a use case."""

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    use_case_id = Column(
        Integer, ForeignKey("use_cases.id", ondelete="CASCADE"), nullable=False
    )

    # Section 1 — Model
    recommended_model = Column(String(100), nullable=False)
    model_provider = Column(String(100), default="")
    model_rationale = Column(Text, nullable=True)
    model_strengths = Column(JSON, nullable=True)       # list[str]
    model_limitations = Column(JSON, nullable=True)    # list[str]

    # Section 2 — Cloud
    recommended_cloud = Column(String(50), nullable=False)
    recommended_region = Column(String(150), nullable=True)
    region = Column(String(100), nullable=True)        # legacy alias
    cloud_rationale = Column(Text, nullable=True)
    cloud_services = Column(JSON, nullable=True)       # list[CloudService dicts]

    # Section 3 — Cost
    estimated_monthly_cost = Column(Float, nullable=False, default=0.0)
    baseline_cost = Column(Float, default=0.0)
    cost_breakdown = Column(JSON, nullable=True)       # CostBreakdown dict
    within_budget = Column(Boolean, nullable=True)

    # Section 4 — Development Guide
    development_guide = Column(JSON, nullable=True)    # list[DevPhase dicts]

    # Section 5 — Architecture
    architecture_summary = Column(Text, nullable=True)
    architecture_components = Column(JSON, nullable=True)  # list[str]
    data_flow = Column(JSON, nullable=True)                # list[str]

    # Section 6 — Compliance
    compliance_flags = Column(JSON, nullable=True)         # list[ComplianceFlag dicts]
    security_recommendations = Column(JSON, nullable=True) # list[str]

    # Section 7 — Alternatives
    alternatives = Column(JSON, nullable=True)             # list[Alternative dicts]

    # Section 8 — Metadata
    confidence_score = Column(Integer, default=0)
    confidence_reasoning = Column(Text, nullable=True)
    missing_info_impact = Column(Text, nullable=True)

    # Legacy / fallback field
    rationale = Column(Text, nullable=True)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    use_case = relationship("UseCase", back_populates="recommendation")
    feedback = relationship(
        "Feedback",
        back_populates="recommendation",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, model={self.recommended_model}, cloud={self.recommended_cloud})>"


class Feedback(Base):
    """Stores user feedback on recommendations."""

    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(
        Integer,
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating = Column(Boolean, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    recommendation = relationship("Recommendation", back_populates="feedback")

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, rating={self.rating})>"
