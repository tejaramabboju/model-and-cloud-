"""
Dashboard router — aggregated statistics for the advisor dashboard.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UseCase, Recommendation, Feedback
from app.schemas import (
    DashboardStats,
    ModelDistribution,
    CloudDistribution,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard-stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Return aggregated statistics for the dashboard:
    - total_use_cases
    - total_monthly_spend (sum of estimated_monthly_cost)
    - total_savings (sum of baseline_cost - estimated_monthly_cost)
    - avg_confidence
    - recommendation_accuracy (% of positive feedback)
    - model_distribution
    - cloud_distribution
    """
    try:
        # ── Total use cases ──────────────────────────────────────────────
        total_result = db.execute(select(func.count(UseCase.id)))
        total_use_cases = total_result.scalar() or 0

        # ── Spend and savings aggregates ─────────────────────────────────
        spend_result = db.execute(
            select(
                func.coalesce(func.sum(Recommendation.estimated_monthly_cost), 0.0),
                func.coalesce(
                    func.sum(
                        Recommendation.baseline_cost
                        - Recommendation.estimated_monthly_cost
                    ),
                    0.0,
                ),
                func.coalesce(func.avg(Recommendation.confidence_score), 0.0),
            )
        )
        row = spend_result.one()
        total_monthly_spend = float(row[0])
        total_savings = float(row[1])
        avg_confidence = round(float(row[2]), 1)

        # ── Recommendation accuracy (feedback-based) ─────────────────────
        feedback_total_result = db.execute(
            select(func.count(Feedback.id))
        )
        feedback_total = feedback_total_result.scalar() or 0

        recommendation_accuracy = None
        if feedback_total > 0:
            positive_result = db.execute(
                select(func.count(Feedback.id)).where(Feedback.rating == True)  # noqa: E712
            )
            positive_count = positive_result.scalar() or 0
            recommendation_accuracy = round(
                (positive_count / feedback_total) * 100, 1
            )

        # ── Model distribution ───────────────────────────────────────────
        model_dist_result = db.execute(
            select(
                Recommendation.recommended_model,
                func.count(Recommendation.id),
            )
            .group_by(Recommendation.recommended_model)
            .order_by(func.count(Recommendation.id).desc())
        )
        model_distribution = [
            ModelDistribution(model=row[0], count=row[1])
            for row in model_dist_result.all()
        ]

        # ── Cloud distribution ───────────────────────────────────────────
        cloud_dist_result = db.execute(
            select(
                Recommendation.recommended_cloud,
                func.count(Recommendation.id),
            )
            .group_by(Recommendation.recommended_cloud)
            .order_by(func.count(Recommendation.id).desc())
        )
        cloud_distribution = [
            CloudDistribution(cloud=row[0], count=row[1])
            for row in cloud_dist_result.all()
        ]

        return DashboardStats(
            total_use_cases=total_use_cases,
            total_monthly_spend=round(total_monthly_spend, 2),
            total_savings=round(total_savings, 2),
            avg_confidence=avg_confidence,
            recommendation_accuracy=recommendation_accuracy,
            model_distribution=model_distribution,
            cloud_distribution=cloud_distribution,
        )

    except Exception as e:
        logger.exception("Error computing dashboard stats")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute dashboard stats: {str(e)}",
        )
