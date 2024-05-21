# Create a fast api router to get the institutions, users must be authenticated
from fastapi import APIRouter
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    UserJobPostingComparisonPublic,
    UserJobPostingComparisonsPublic,
    UserJobPostingComparisons,
)
from sqlmodel import select

router = APIRouter()


@router.get("/", response_model=UserJobPostingComparisonPublic)
def get_user_job_posting_comparisons(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 30
):
    query = (
        select(UserJobPostingComparisons)
        .where(UserJobPostingComparisons.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )

    comparisons = session.exec(query).all()

    public_comparisons = [
        UserJobPostingComparisonPublic.model_validate(comparison)
        for comparison in comparisons
    ]
    return UserJobPostingComparisonsPublic(data=public_comparisons)
