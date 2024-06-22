# Create a fast api router to get the institutions, users must be authenticated
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from fastapi import APIRouter, HTTPException
from app.core.utils import encode_pdf_to_base64
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    UserJobPostingComparisonBase,
    UserJobPostingComparisonPublic,
    UserJobPostingComparisonsPublic,
    UserJobPostingComparisonPublicDetail,
    UserJobPostingComparisons,
    Message,
    ModelParameters,
)
from app.llm.cv_builder import CVBuilder
from app.llm.cover_letter_builder import CoverLetterBuilder
from app.api.routes.job_postings import extract_job_postings
from sqlmodel import select

router = APIRouter()


@router.get("/current_user", response_model=UserJobPostingComparisonsPublic)
def get_user_job_posting_comparisons(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 30
):
    query = (
        select(UserJobPostingComparisons)
        .where(
            UserJobPostingComparisons.user_id == current_user.id
            and UserJobPostingComparisons.is_active
        )
        .offset(skip)
        .limit(limit)
        .options(joinedload(UserJobPostingComparisons.job_posting))
    )

    comparisons = session.exec(query).all()

    public_comparisons = [
        UserJobPostingComparisonPublic(
            **comparison.model_dump(),
            title=comparison.job_posting.title,
            company=comparison.job_posting.company,
            location=comparison.job_posting.location,
        )
        for comparison in comparisons
    ]
    return UserJobPostingComparisonsPublic(data=public_comparisons)


@router.get("/", response_model=UserJobPostingComparisonPublicDetail)
def get_user_job_posting_comparison_by_id(
    session: SessionDep,
    current_user: CurrentUser,
    id: int | None = None,
    job_posting_id: int | None = None,
):
    statement = (
        select(UserJobPostingComparisons)
        .options(joinedload(UserJobPostingComparisons.job_posting))
        .options(joinedload(UserJobPostingComparisons.work_experiences))
        .options(joinedload(UserJobPostingComparisons.cover_letter_paragraphs))
    )

    if id is not None:
        statement = statement.where(UserJobPostingComparisons.id == id)

    if job_posting_id is not None:
        statement = statement.where(
            UserJobPostingComparisons.job_posting_id == job_posting_id
        )

    comparison = session.scalars(statement).unique().one_or_none()
    if comparison:
        print(comparison.work_experiences)

        if comparison.resume:
            comparison.resume = encode_pdf_to_base64(comparison.resume)
        if comparison.cover_letter:
            comparison.cover_letter = encode_pdf_to_base64(comparison.cover_letter)
        return UserJobPostingComparisonPublicDetail(
            **comparison.model_dump(),
            title=comparison.job_posting.title,
            company=comparison.job_posting.company,
            location=comparison.job_posting.location,
            work_experiences=comparison.work_experiences,
            cover_letter_paragraphs=comparison.cover_letter_paragraphs,
        )
    else:
        raise HTTPException(status_code=404, detail="Comparison not found")


@router.patch("/create-activate", response_model=Message)
def create_or_activate_user_job_posting_comparison(
    session: SessionDep,
    current_user: CurrentUser,
    job_posting_id: int,
):
    try:
        statement = select(UserJobPostingComparisons).where(
            UserJobPostingComparisons.user_id == current_user.id,
            UserJobPostingComparisons.job_posting_id == job_posting_id,
        )
        existing_comparison = session.exec(statement).one_or_none()

        if existing_comparison:
            existing_comparison.is_active = True
            session.add(existing_comparison)
            session.commit()
            return Message(message="Comparison Activated back again")

        comparison = UserJobPostingComparisons(
            user_id=current_user.id,
            job_posting_id=job_posting_id,
        )
        session.add(comparison)
        session.commit()
        session.refresh(comparison)
        return Message(message="Comparison Created")
    except IntegrityError:
        session.rollback()
        return Message(message="Comparison already exists")
    except Exception as e:
        session.rollback()
        return Message(message=str(e))


@router.post("/generate-resume", response_model=Message)
def generate_resume(
    session: SessionDep,
    current_user: CurrentUser,
    comparison_id: int,
    model_in: ModelParameters,
):
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")
    statement = select(UserJobPostingComparisons).where(
        UserJobPostingComparisons.id == comparison_id,
    )
    comparison = session.exec(statement).one_or_none()
    if not comparison or not comparison.job_posting_id:
        return Message(message="Comparison does not exist or job posting id is missing")

    # Ensure the job posting summary is extracted
    extract_job_postings(
        session=session,
        current_user=current_user,
        job_posting_id=comparison.job_posting_id,
        model_in=model_in,
    )

    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Use your CVBuilder to generate the CV and cover letter
    cv_builder = CVBuilder(
        model_name=model_in.get_value(),  # Replace with actual model name
        user_id=current_user.id,
        temperature=model_in.temperature,
    )
    cv_builder.build(job_ids=[comparison.job_posting_id])
    return Message(message="Resume generated successfully")


@router.post("/generate-cover-letter", response_model=Message)
def generate_cover_letter(
    session: SessionDep,
    current_user: CurrentUser,
    comparison_id: int,
    model_in: ModelParameters,
):
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")
    statement = select(UserJobPostingComparisons).where(
        UserJobPostingComparisons.id == comparison_id,
    )
    comparison = session.exec(statement).one_or_none()
    if not comparison or not comparison.job_posting_id:
        return Message(message="Comparison does not exist or job posting id is missing")

    # Ensure the job posting summary is extracted
    extract_job_postings(
        session=session,
        current_user=current_user,
        job_posting_id=comparison.job_posting_id,
        model_in=model_in,
    )
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    cover_letter_builder = CoverLetterBuilder(
        model_name=model_in.get_value(),  # Replace with actual model name
        user_id=current_user.id,
        temperature=model_in.temperature,
    )

    cover_letter_builder.build(job_ids=[comparison.job_posting_id])
    return Message(message="Cover letter generated successfully")


@router.patch("/deactivate", response_model=Message)
def deactivate_user_job_posting_comparison(
    session: SessionDep,
    current_user: CurrentUser,
    job_posting_id: int,
):
    try:
        statement = select(UserJobPostingComparisons).where(
            UserJobPostingComparisons.user_id == current_user.id,
            UserJobPostingComparisons.job_posting_id == job_posting_id,
        )
        existing_comparison = session.exec(statement).one_or_none()

        if existing_comparison:
            existing_comparison.is_active = False
            session.add(existing_comparison)
            session.commit()
            return Message(message="Comparison deactivated")
        else:
            return Message(message="Comparison does not exist")
    except Exception as e:
        session.rollback()
        return Message(message=str(e))
