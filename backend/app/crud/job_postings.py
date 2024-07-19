from sqlmodel import Session, select, col, func

from app.logger import Logger
from app.models import (
    JobQueryParams,
    Institutions,
    JobPostings,
    SeniorityLevels,
    EmploymentTypes,
    ExperienceLevels,
    RemoteModalities,
    SalaryRangeFilters,
    InstitutionSizes,
)

logger = Logger(prefix="JobPostingsCRUD", log_file_name="crud.log").get_logger()


def get_job_posting_by_id(session: Session, job_posting_id: int) -> JobPostings:
    job_posting = session.exec(
        select(JobPostings).where(JobPostings.id == job_posting_id)
    ).one_or_none()
    if not job_posting:
        logger.error(f"Job posting {job_posting_id} not found")
        raise ValueError(f"Job posting {job_posting_id} not found")
    return job_posting


def get_job_postings_by_similarity(
    session: Session, params: JobQueryParams
) -> JobPostings:
    """
    Get job postings based on query parameters.
    """
    query = (
        select(  # type: ignore
            JobPostings.id,
            JobPostings.title,
            JobPostings.company,
            JobPostings.company_url,
            JobPostings.location,
            JobPostings.description,
            col(SeniorityLevels.description).label("seniority_level"),
            col(EmploymentTypes.description).label("employment_type"),
            col(ExperienceLevels.description).label("experience_level"),
            col(RemoteModalities.description).label("remote_modality"),
            col(SalaryRangeFilters.description).label("salary_range"),
            JobPostings.industries,
            JobPostings.job_functions,
            JobPostings.skills,
            JobPostings.job_salary_min,
            JobPostings.job_salary_max,
            JobPostings.job_poster_name,
            JobPostings.job_poster_profile,
            JobPostings.summary,
            col(Institutions.about).label("institution_about"),
            col(Institutions.website).label("institution_website"),
            col(Institutions.industry).label("institution_industry"),
            col(InstitutionSizes.description).label("institution_size"),
            col(Institutions.followers).label("institution_followers"),
            col(Institutions.employees).label("institution_employees"),
            col(Institutions.tagline).label("institution_tagline"),
            col(Institutions.location).label("institution_location"),
        )
        .join(Institutions, JobPostings.institution_id == Institutions.id, isouter=True)
        .join(
            SeniorityLevels,
            JobPostings.seniority_level_id == SeniorityLevels.id,
            isouter=True,
        )
        .join(
            EmploymentTypes,
            JobPostings.employment_type_id == EmploymentTypes.id,
            isouter=True,
        )
        .join(
            ExperienceLevels,
            JobPostings.experience_level_id == ExperienceLevels.id,
            isouter=True,
        )
        .join(
            RemoteModalities,
            JobPostings.remote_modality_id == RemoteModalities.id,
            isouter=True,
        )
        .join(
            SalaryRangeFilters,
            JobPostings.salary_range_id == SalaryRangeFilters.id,
            isouter=True,
        )
        .join(
            InstitutionSizes, Institutions.size_id == InstitutionSizes.id, isouter=True
        )
    )

    if params.job_title:
        query = query.order_by(
            func.similarity(JobPostings.title, params.job_title).desc()
        )
    if params.company_name:
        query = query.order_by(
            func.similarity(JobPostings.company, params.company_name).desc()
        )

    query = query.offset(params.skip).limit(params.limit)

    return session.exec(query).all()


def create_job_posting(*, session: Session, job_posting_in: JobPostings) -> JobPostings:
    session.add(job_posting_in)
    session.commit()
    session.refresh(job_posting_in)
    logger.info(f"Job posting {job_posting_in.id} created")
    return job_posting_in


def get_job_posting_complete_by_id(
    session: Session,
    job_posting_id: int,
    job_posting_columns: list[str],
    institution_columns: list[str],
):
    job_posting = session.exec(
        select(  # type: ignore
            *job_posting_columns,
            *institution_columns,
            col(InstitutionSizes.description).label("institution_size"),
            col(EmploymentTypes.description).label("employment_type"),
            col(SeniorityLevels.description).label("seniority_level"),
        )
        .outerjoin(
            Institutions,
            JobPostings.company_url == Institutions.url,  # type: ignore
        )
        .outerjoin(
            InstitutionSizes,
            Institutions.size_id == InstitutionSizes.id,  # type: ignore
        )
        .outerjoin(
            SeniorityLevels,
            JobPostings.seniority_level_id == SeniorityLevels.id,  # type: ignore
        )
        .outerjoin(
            EmploymentTypes,
            JobPostings.employment_type_id == EmploymentTypes.id,  # type: ignore
        )
        .where(JobPostings.id == job_posting_id)  # type: ignore
    ).first()
    if not job_posting:
        logger.error(f"Job posting {job_posting_id} not found")
        raise ValueError(f"Job posting {job_posting_id} not found")
    return job_posting
