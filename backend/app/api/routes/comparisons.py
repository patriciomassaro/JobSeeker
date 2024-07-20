from fastapi import APIRouter, HTTPException
from app.api.decorators import require_positive_balance
from app.core.utils import encode_pdf_to_base64
from app.api.deps import CurrentUser, SessionDep
from app.crud.comparisons import (
    get_active_comparisons,
    get_ordered_work_experiences,
    get_comparison_by_id_or_job_posting_id,
    get_ordered_cover_letter_paragraphs,
    get_work_experience_by_id,
    edit_work_experience,
    create_work_experience_example,
    get_cover_letter_paragraph_by_id,
    create_cover_letter_paragraph_example,
    edit_cover_letter_paragraph,
)
from app.models import (
    ComparisonPublic,
    ComparisonsPublic,
    ComparisonPublicDetail,
    Comparisons,
    Message,
    ModelParameters,
    WorkExperiencePublic,
    CoverLetterParagraphPublic,
)
from app.llm.work_experience_generator import WorkExperienceGenerator
from app.llm.cover_letter_generator import CoverLetterGenerator
from app.llm.resume_builder import ResumeBuilder
from app.llm.cover_letter_builder import CoverLetterBuilder
from app.api.routes.job_postings import extract_job_posting

router = APIRouter()


@router.get("/current_user", response_model=ComparisonsPublic)
async def get_comparisons(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 30
):
    """
    Get the comparisons activated by the current user
    """
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")
    comparisons = get_active_comparisons(session, current_user.id, skip, limit)
    public_comparisons = [
        ComparisonPublic(
            **comparison.model_dump(),
            title=comparison.job_posting.title,
            company=comparison.job_posting.company,
            location=comparison.job_posting.location,
        )
        for comparison in comparisons
    ]
    return ComparisonsPublic(data=public_comparisons)


@router.get("/", response_model=ComparisonPublicDetail)
async def get_comparison_by_id(
    session: SessionDep,
    current_user: CurrentUser,
    comparison_id: int | None = None,
    job_posting_id: int | None = None,
):
    """Get the comparison by id or by a combination of user_id and job_posting_id"""
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")
    comparison = get_comparison_by_id_or_job_posting_id(
        session,
        user_id=current_user.id,
        comparison_id=comparison_id,
        job_posting_id=job_posting_id,
    )
    if comparison:
        comparison.work_experiences = get_ordered_work_experiences(
            session, comparison.id
        )

        comparison.cover_letter_paragraphs = get_ordered_cover_letter_paragraphs(
            session, comparison.id
        )

        if comparison.resume:
            comparison.resume = encode_pdf_to_base64(comparison.resume)  # type: ignore
        if comparison.cover_letter:
            comparison.cover_letter = encode_pdf_to_base64(comparison.cover_letter)  # type: ignore

        return ComparisonPublicDetail(
            **comparison.model_dump(),
            title=comparison.job_posting.title,
            company=comparison.job_posting.company,
            location=comparison.job_posting.location,
            work_experiences=comparison.work_experiences,  # type: ignore
            cover_letter_paragraphs=comparison.cover_letter_paragraphs,  # type: ignore
        )
    else:
        raise HTTPException(status_code=404, detail="Comparison not found")


@router.patch("/create-activate", response_model=Message)
async def create_or_activate_comparison(
    session: SessionDep,
    current_user: CurrentUser,
    job_posting_id: int,
):
    """
    Create a comparison for the job and user if it does not exists, or activate it if it exists and is not active
    """
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")
    existing_comparison = get_comparison_by_id_or_job_posting_id(
        session, user_id=current_user.id, job_posting_id=job_posting_id
    )

    if existing_comparison:
        existing_comparison.is_active = True
        session.add(existing_comparison)
        session.commit()
        return Message(message="Comparison Activated back again")

    comparison = Comparisons(
        user_id=current_user.id,
        job_posting_id=job_posting_id,
    )
    session.add(comparison)
    session.commit()
    session.refresh(comparison)
    return Message(message="Comparison Created")


@router.post("/generate-work-experiences", response_model=Message)
@require_positive_balance()
async def generate_resume(
    session: SessionDep,
    current_user: CurrentUser,
    comparison_id: int,
    model_in: ModelParameters,
):
    """
    Generate the work experiences that will be used to create the custom resume.
    """
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")

    comparison = get_comparison_by_id_or_job_posting_id(
        session=session, user_id=current_user.id, comparison_id=comparison_id
    )

    if not comparison or not comparison.job_posting_id:
        return Message(message="Comparison does not exist or job posting id is missing")

    extract_job_posting(
        session=session,
        current_user=current_user,
        job_posting_id=comparison.job_posting_id,
        model_in=model_in,
    )

    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    generator = WorkExperienceGenerator(
        model_name=model_in.name,
        user_id=current_user.id,
        temperature=model_in.temperature,
        job_posting_id=comparison.job_posting_id,
        comparison_id=comparison.id,
    )
    generator.generate_work_experiences()

    return Message(message="work experiences generated successfully")


@router.patch("/build-resume", response_model=Message)
async def build_resume(current_user: CurrentUser, comparison_id: int):
    """
    Build the CV Using the current user information and the work experiences
    """
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")
    builder = ResumeBuilder(
        user_id=current_user.id,
        comparison_id=comparison_id,
    )
    builder.build_resume()
    return Message(message="Resume built successfully")


@require_positive_balance()
@router.post("/generate-cover-letter-paragraphs", response_model=Message)
@require_positive_balance()
async def generate_cover_letter(
    session: SessionDep,
    current_user: CurrentUser,
    comparison_id: int,
    model_in: ModelParameters,
):
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")

    comparison = get_comparison_by_id_or_job_posting_id(
        session=session, user_id=current_user.id, comparison_id=comparison_id
    )

    if not comparison or not comparison.id or not comparison.job_posting_id:
        return Message(message="Comparison does not exist")

    # Ensure the job posting summary is extracted
    extract_job_posting(
        session=session,
        current_user=current_user,
        job_posting_id=comparison.job_posting_id,
        model_in=model_in,
    )

    cover_letter_generator = CoverLetterGenerator(
        model_name=model_in.name,
        user_id=current_user.id,
        temperature=model_in.temperature,
        job_posting_id=comparison.job_posting_id,
        comparison_id=comparison.id,
    )

    cover_letter_generator.generate_cover_letter_paragraphs()

    return Message(message="Cover letter paragraphs generated successfully")


@router.patch("/build-cover-letter", response_model=Message)
async def build_cover_letter(current_user: CurrentUser, comparison_id: int):
    """
    Build the Cover Letter Using the current user information and the cover letter paragraphs
    """
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")
    builder = CoverLetterBuilder(
        user_id=current_user.id,
        comparison_id=comparison_id,
    )
    builder.build_cover_letter()
    return Message(message="Cover Letter built successfully")


@router.patch("/deactivate", response_model=Message)
async def deactivate_comparison(
    session: SessionDep,
    current_user: CurrentUser,
    job_posting_id: int,
):
    """
    Deactivate the comparison for the job and user if it exists and is active
    """
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        existing_comparison = get_comparison_by_id_or_job_posting_id(
            session=session, user_id=current_user.id, job_posting_id=job_posting_id
        )

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


@router.post("/edit-work-experience", response_model=Message)
async def api_edit_work_experience(
    session: SessionDep,
    current_user: CurrentUser,
    new_work_experience: WorkExperiencePublic,
):
    print(new_work_experience)
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")

    if new_work_experience.start_year is None:
        raise HTTPException(status_code=400, detail="Start year is required")
    if new_work_experience.title is None:
        raise HTTPException(status_code=400, detail="Title is required")

    old_work_experience = get_work_experience_by_id(
        session=session, work_experience_id=new_work_experience.id
    )
    if not old_work_experience:
        raise HTTPException(status_code=404, detail="Work Experience not found")

    _ = create_work_experience_example(
        session=session,
        old_work_experience=old_work_experience,
        new_work_experience=new_work_experience,
    )

    _ = edit_work_experience(
        session=session,
        old_work_experience=old_work_experience,
        new_work_experience=new_work_experience,
    )

    return Message(message="Work Experience edited successfully")


@router.post("/edit-cover-letter-paragraph", response_model=Message)
async def api_edit_cover_letter_paragraph(
    session: SessionDep,
    current_user: CurrentUser,
    new_cover_letter_paragraph: CoverLetterParagraphPublic,
):
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")

    old_cover_letter_paragraph = get_cover_letter_paragraph_by_id(
        session=session, paragraph_id=new_cover_letter_paragraph.id
    )
    if not old_cover_letter_paragraph:
        raise HTTPException(
            status_code=404, detail="Cover Letter Paragraph to edit does not exist"
        )
    _ = create_cover_letter_paragraph_example(
        session=session,
        old_cover_letter_paragraph=old_cover_letter_paragraph,
        new_cover_letter_paragraph=new_cover_letter_paragraph,
    )

    _ = edit_cover_letter_paragraph(
        session=session,
        old_cover_letter_paragraph=old_cover_letter_paragraph,
        new_cover_letter_paragraph=new_cover_letter_paragraph,
    )

    return Message(message="Cover Letter edited successfully")
