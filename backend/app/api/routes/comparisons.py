from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from fastapi import APIRouter, HTTPException
from app.core.utils import encode_pdf_to_base64
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    ComparisonPublic,
    ComparisonsPublic,
    ComparisonPublicDetail,
    Comparisons,
    Message,
    ModelParameters,
    WorkExperiencePublic,
    WorkExperiences,
    WorkExperienceExamples,
    CoverLetterParagraphPublic,
    CoverLetterParagraphs,
    CoverLetterParagraphExamples,
)
from app.llm.work_experience_generator import WorkExperienceGenerator
from app.llm.cover_letter_generator import CoverLetterGenerator
from app.llm.resume_builder import ResumeBuilder
from app.llm.cover_letter_builder import CoverLetterBuilder
from app.api.routes.job_postings import extract_job_posting
from sqlmodel import select, desc, case, asc

router = APIRouter()


@router.get("/current_user", response_model=ComparisonsPublic)
def get_comparisons(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 30
):
    """
    Get the comparisons activated by the current user
    """
    query = (
        select(Comparisons)
        .where(Comparisons.user_id == current_user.id and Comparisons.is_active)
        .offset(skip)
        .limit(limit)
        .options(joinedload(Comparisons.job_posting))
    )

    comparisons = session.exec(query).all()

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
def get_comparison_by_id(
    session: SessionDep,
    current_user: CurrentUser,
    comparison_id: int | None = None,
    job_posting_id: int | None = None,
):
    """Get the comparison by id or by a combination of user_id and job_posting_id"""

    statement = select(Comparisons).options(joinedload(Comparisons.job_posting))

    if comparison_id is not None:
        statement = statement.where(Comparisons.id == comparison_id)

    if job_posting_id is not None:
        statement = statement.where(
            Comparisons.job_posting_id == job_posting_id
            and Comparisons.user_id == current_user.id
        )

    comparison = session.scalars(statement).unique().one_or_none()
    if comparison:
        # Fetch and order work experiences
        work_experiences_query = (
            select(WorkExperiences)
            .where(WorkExperiences.comparison_id == comparison.id)
            .order_by(
                desc(
                    case(
                        (WorkExperiences.end_year.is_(None), 9999),  # type: ignore
                        else_=WorkExperiences.end_year,
                    )
                ),
                desc(
                    case(
                        (WorkExperiences.end_month.is_(None), 12),  # type: ignore
                        else_=WorkExperiences.end_month,
                    )
                ),
                desc(WorkExperiences.start_year),
                desc(WorkExperiences.start_month),
            )
        )
        ordered_work_experiences = session.scalars(work_experiences_query).all()
        comparison.work_experiences = ordered_work_experiences  # type: ignore

        # Fetch and order cover letter paragraphs
        cover_letter_paragraphs_query = (
            select(CoverLetterParagraphs)
            .where(CoverLetterParagraphs.comparison_id == comparison.id)
            .order_by(asc(CoverLetterParagraphs.paragraph_number))
        )
        ordered_cover_letter_paragraphs = session.scalars(
            cover_letter_paragraphs_query
        ).all()
        comparison.cover_letter_paragraphs = ordered_cover_letter_paragraphs  # type: ignore

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
def create_or_activate_comparison(
    session: SessionDep,
    current_user: CurrentUser,
    job_posting_id: int,
):
    """
    Create a comparison for the job and user if it does not exists, or activate it if it exists and is not active
    """
    try:
        statement = select(Comparisons).where(
            Comparisons.user_id == current_user.id,
            Comparisons.job_posting_id == job_posting_id,
        )
        existing_comparison = session.exec(statement).one_or_none()

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
    except IntegrityError:
        session.rollback()
        return Message(message="Comparison already exists")
    except Exception as e:
        session.rollback()
        return Message(message=str(e))


@router.post("/generate-work-experiences", response_model=Message)
def generate_resume(
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
    statement = select(Comparisons).where(
        Comparisons.id == comparison_id,
    )
    comparison = session.exec(statement).one_or_none()
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
def build_resume(current_user: CurrentUser, comparison_id: int):
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


@router.post("/generate-cover-letter-paragraphs", response_model=Message)
def generate_cover_letter(
    session: SessionDep,
    current_user: CurrentUser,
    comparison_id: int,
    model_in: ModelParameters,
):
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")
    statement = select(Comparisons).where(
        Comparisons.id == comparison_id,
    )
    comparison = session.exec(statement).one_or_none()
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
def build_cover_letter(current_user: CurrentUser, comparison_id: int):
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
def deactivate_comparison(
    session: SessionDep,
    current_user: CurrentUser,
    job_posting_id: int,
):
    """
    Deactivate the comparison for the job and user if it exists and is active
    """
    try:
        statement = select(Comparisons).where(
            Comparisons.user_id == current_user.id,
            Comparisons.job_posting_id == job_posting_id,
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


@router.post("/edit-work-experience", response_model=Message)
def edit_work_experience(
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

    statement = select(WorkExperiences).where(
        WorkExperiences.id == new_work_experience.id,
    )
    old_work_experience = session.exec(statement).one_or_none()
    if not old_work_experience:
        raise HTTPException(status_code=404, detail="Work Experience not found")

    # Create an example
    example = WorkExperienceExamples(
        comparison_id=old_work_experience.comparison_id,
        original_title=old_work_experience.title,
        original_accomplishments=old_work_experience.accomplishments,
        edited_title=new_work_experience.title,
        edited_accomplishments=new_work_experience.accomplishments,
    )
    session.add(example)
    old_work_experience.title = new_work_experience.title
    old_work_experience.company = new_work_experience.company
    old_work_experience.start_year = new_work_experience.start_year
    old_work_experience.start_month = new_work_experience.start_month
    old_work_experience.end_year = new_work_experience.end_year
    old_work_experience.end_month = new_work_experience.end_month
    old_work_experience.accomplishments = new_work_experience.accomplishments
    session.add(old_work_experience)
    session.commit()

    return Message(message="Work Experience edited successfully")


@router.post("/edit-cover-letter-paragraph", response_model=Message)
def edit_cover_letter_paragraph(
    session: SessionDep,
    current_user: CurrentUser,
    new_cover_letter_paragraph: CoverLetterParagraphPublic,
):
    if not current_user.id:
        raise HTTPException(status_code=404, detail="User not found")

    statement = select(CoverLetterParagraphs).where(
        CoverLetterParagraphs.id == new_cover_letter_paragraph.id,
    )
    old_cover_letter_paragraph = session.exec(statement).one_or_none()
    if not old_cover_letter_paragraph:
        raise HTTPException(
            status_code=404, detail="Cover Letter Paragraph to edit does not exist"
        )

    # Create an example
    example = CoverLetterParagraphExamples(
        comparison_id=old_cover_letter_paragraph.comparison_id,
        paragraph_number=old_cover_letter_paragraph.paragraph_number,
        original_paragraph_text=old_cover_letter_paragraph.paragraph_text,
        edited_paragraph_text=new_cover_letter_paragraph.paragraph_text,
    )
    session.add(example)
    old_cover_letter_paragraph.paragraph_text = (
        new_cover_letter_paragraph.paragraph_text
    )
    session.add(old_cover_letter_paragraph)
    session.commit()

    return Message(message="Cover Letter edited successfully")
