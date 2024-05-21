# Create a fast api router to get the institutions, users must be authenticated
from fastapi import APIRouter
from app.api.deps import CurrentUser, SessionDep
from app.models import JobPostingsPublic, JobPostings, JobPostingPublic
from sqlmodel import select

router = APIRouter()


@router.get("/", response_model=JobPostingsPublic)
def get_institutions(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 30
):
    print(skip, limit)
    statement = select(JobPostings).offset(skip).limit(limit)
    institutions = session.exec(statement).all()

    public_institutions = [
        JobPostingPublic.model_validate(institution) for institution in institutions
    ]
    return JobPostingsPublic(data=public_institutions)
