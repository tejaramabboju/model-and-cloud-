"""
Feedback router — handles user feedback on recommendations.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Recommendation, Feedback
from app.schemas import FeedbackSubmit, FeedbackResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    payload: FeedbackSubmit,
    db: Session = Depends(get_db),
):
    """
    Submit feedback (thumbs up/down + optional comment) for a recommendation.
    Validates that the recommendation exists before storing.
    """
    try:
        # Validate that the recommendation exists
        result = db.execute(
            select(Recommendation).where(
                Recommendation.id == payload.recommendation_id
            )
        )
        recommendation = result.scalar_one_or_none()

        if recommendation is None:
            raise HTTPException(
                status_code=404,
                detail=f"Recommendation with id {payload.recommendation_id} not found.",
            )

        # Check if feedback already exists for this recommendation
        existing_result = db.execute(
            select(Feedback).where(
                Feedback.recommendation_id == payload.recommendation_id
            )
        )
        existing_feedback = existing_result.scalar_one_or_none()

        if existing_feedback:
            # Update existing feedback
            existing_feedback.rating = payload.rating
            existing_feedback.comment = payload.comment
            existing_feedback.created_at = datetime.now(timezone.utc)
            db.flush()

            return FeedbackResponse(
                id=existing_feedback.id,
                recommendation_id=existing_feedback.recommendation_id,
                rating=existing_feedback.rating,
                comment=existing_feedback.comment,
                created_at=existing_feedback.created_at,
            )

        # Create new feedback
        feedback = Feedback(
            recommendation_id=payload.recommendation_id,
            rating=payload.rating,
            comment=payload.comment,
            created_at=datetime.now(timezone.utc),
        )
        db.add(feedback)
        db.flush()

        return FeedbackResponse(
            id=feedback.id,
            recommendation_id=feedback.recommendation_id,
            rating=feedback.rating,
            comment=feedback.comment,
            created_at=feedback.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error submitting feedback")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit feedback: {str(e)}",
        )
