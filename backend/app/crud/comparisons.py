from sqlmodel import Session, select, col, func, desc, asc, case
from sqlalchemy.orm import joinedload
from app.logger import Logger
from app.models import (
    Comparisons,
    WorkExperiences,
    WorkExperiencePublic,
    WorkExperienceExamples,
    CoverLetterParagraphs,
    CoverLetterParagraphPublic,
    CoverLetterParagraphExamples,
)

logger = Logger(prefix="ComparisonCRUD", log_file_name="crud.log").get_logger()


def get_active_comparisons(
    session: Session, user_id: int, skip: int, limit: int
) -> list[Comparisons]:
    query = (
        select(Comparisons)
        .where(Comparisons.user_id == user_id and Comparisons.is_active)
        .offset(skip)
        .limit(limit)
        .options(joinedload(Comparisons.job_posting))
    )

    return list(session.exec(query).all())


def get_comparison_by_id_or_job_posting_id(
    session: Session,
    user_id: int,
    comparison_id: int | None = None,
    job_posting_id: int | None = None,
) -> Comparisons | None:
    if comparison_id is None and job_posting_id is None:
        logger.error("Either comparison_id or job_posting_id is required")
        raise ValueError("Either comparison_id or job_posting_id is required")
    statement = select(Comparisons).options(joinedload(Comparisons.job_posting))

    if comparison_id is not None:
        statement = statement.where(Comparisons.id == comparison_id)

    if job_posting_id is not None:
        statement = statement.where(
            Comparisons.job_posting_id == job_posting_id
            and Comparisons.user_id == user_id
        )

    return session.scalars(statement).unique().one_or_none()


def get_ordered_work_experiences(
    session: Session, comparison_id: int
) -> list[WorkExperiences]:
    work_experiences_query = (
        select(WorkExperiences)
        .where(WorkExperiences.comparison_id == comparison_id)
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
    return list(session.scalars(work_experiences_query).all())


def get_work_experience_by_id(
    session: Session, work_experience_id: int
) -> WorkExperiences | None:
    return session.exec(
        select(WorkExperiences).where(WorkExperiences.id == work_experience_id)
    ).one_or_none()


def get_cover_letter_paragraph_by_id(
    session: Session, paragraph_id: int
) -> CoverLetterParagraphs | None:
    return session.exec(
        select(CoverLetterParagraphs).where(CoverLetterParagraphs.id == paragraph_id)
    ).one_or_none()


def create_work_experience_example(
    session: Session,
    old_work_experience: WorkExperiencePublic,
    new_work_experience: WorkExperiencePublic,
) -> WorkExperienceExamples:
    example = WorkExperienceExamples(
        comparison_id=old_work_experience.comparison_id,
        original_title=old_work_experience.title,
        original_accomplishments=old_work_experience.accomplishments,
        edited_title=new_work_experience.title,
        edited_accomplishments=new_work_experience.accomplishments,
    )
    session.add(example)
    session.commit()
    return example


def edit_work_experience(
    session: Session,
    old_work_experience: WorkExperiences,
    new_work_experience: WorkExperiencePublic,
) -> WorkExperiences:
    old_work_experience.title = new_work_experience.title
    old_work_experience.company = new_work_experience.company
    old_work_experience.start_year = new_work_experience.start_year
    old_work_experience.start_month = new_work_experience.start_month
    old_work_experience.end_year = new_work_experience.end_year
    old_work_experience.end_month = new_work_experience.end_month
    old_work_experience.accomplishments = new_work_experience.accomplishments
    session.add(old_work_experience)
    session.commit()
    return old_work_experience


def get_ordered_cover_letter_paragraphs(
    session: Session, comparison_id: int
) -> list[CoverLetterParagraphs]:
    cover_letter_paragraphs_query = (
        select(CoverLetterParagraphs)
        .where(CoverLetterParagraphs.comparison_id == comparison_id)
        .order_by(asc(CoverLetterParagraphs.paragraph_number))
    )
    return list(session.scalars(cover_letter_paragraphs_query).all())


def create_cover_letter_paragraph_example(
    session: Session,
    old_cover_letter_paragraph: CoverLetterParagraphs,
    new_cover_letter_paragraph: CoverLetterParagraphPublic,
):
    example = CoverLetterParagraphExamples(
        comparison_id=old_cover_letter_paragraph.comparison_id,
        paragraph_number=old_cover_letter_paragraph.paragraph_number,
        original_paragraph_text=old_cover_letter_paragraph.paragraph_text,
        edited_paragraph_text=new_cover_letter_paragraph.paragraph_text,
    )
    session.add(example)
    session.commit()
    logger.info(f"Cover letter paragraph example {example.id} created")


def edit_cover_letter_paragraph(
    session: Session,
    old_cover_letter_paragraph: CoverLetterParagraphs,
    new_cover_letter_paragraph: CoverLetterParagraphPublic,
):
    old_cover_letter_paragraph.paragraph_text = (
        new_cover_letter_paragraph.paragraph_text
    )
    session.add(old_cover_letter_paragraph)
    session.commit()
    logger.info(f"Cover letter paragraph {old_cover_letter_paragraph.id} updated")


def create_comparison(session: Session, user_id: int, job_posting_id: int):
    comparison = Comparisons(user_id=user_id, job_posting_id=job_posting_id)
    session.add(comparison)
    session.commit()
    session.refresh(comparison)
    logger.info(f"Comparison {comparison.id} created")

    return comparison
