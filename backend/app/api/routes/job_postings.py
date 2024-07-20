from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import CurrentUser, SessionDep
from app.api.decorators import require_positive_balance
from app.models import (
    JobPostingsPublic,
    JobPostingPublic,
    JobQueryParams,
    Message,
    ModelParameters,
)
from app.crud.job_postings import get_job_postings_by_similarity, get_job_posting_by_id
from app.llm.job_posting_extractor import JobDescriptionLLMExtractor

router = APIRouter()


@router.get("/", response_model=JobPostingsPublic)
async def get_job_postings(
    session: SessionDep, current_user: CurrentUser, params: JobQueryParams = Depends()
):
    """
    Get job postings based on query parameters.
    """
    results = get_job_postings_by_similarity(session=session, params=params)
    jobs = [JobPostingPublic(**row._mapping) for row in results]  # type: ignore
    return JobPostingsPublic(data=jobs)


@router.post("/extract", response_model=Message)
@require_positive_balance()
async def extract_job_posting(
    session: SessionDep,
    current_user: CurrentUser,
    job_posting_id: int,
    model_in: ModelParameters,
):
    """
    Use LLMs to extract and structure job posting data.
    """
    if not current_user:
        return HTTPException(status_code=404, detail="User not found")

    try:
        job_posting = get_job_posting_by_id(
            session=session, job_posting_id=job_posting_id
        )
    except ValueError:
        return HTTPException(status_code=404, detail="Job posting not found")

    if not job_posting.summary:
        extractor = JobDescriptionLLMExtractor(
            model_name=model_in.name,
            temperature=model_in.temperature,
            user_id=current_user.id,  # type: ignore
        )
        extractor.extract_job_posting_and_write_to_db(job_posting_id=job_posting_id)
    return Message(message="Job posting extracted successfully")
