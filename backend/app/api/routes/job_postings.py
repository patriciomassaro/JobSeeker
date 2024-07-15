from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, col
from sqlalchemy import func
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    ExperienceLevels,
    InstitutionSizes,
    JobPostingsPublic,
    JobPostingPublic,
    JobPostings,
    JobQueryParams,
    Message,
    ModelParameters,
    RemoteModalities,
    SeniorityLevels,
    EmploymentTypes,
    SalaryRangeFilters,
    Institutions,
)
from app.llm.job_posting_extractor import JobDescriptionLLMExtractor

router = APIRouter()


@router.get("/", response_model=JobPostingsPublic)
def get_job_postings(
    session: SessionDep, current_user: CurrentUser, params: JobQueryParams = Depends()
):
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

    results = session.exec(query).all()
    jobs = [JobPostingPublic(**row._mapping) for row in results]
    return JobPostingsPublic(data=jobs)


@router.post("/extract", response_model=Message)
def extract_job_posting(
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

    statement = select(JobPostings).where(JobPostings.id == job_posting_id)
    job_posting = session.exec(statement).one_or_none()
    if job_posting is None:
        return HTTPException(status_code=404, detail="Job posting not found")
    if not job_posting.summary:
        extractor = JobDescriptionLLMExtractor(
            model_name=model_in.name,
            temperature=model_in.temperature,
            user_id=current_user.id,  # type: ignore
        )
        extractor.extract_job_posting_and_write_to_db(job_id=job_posting_id)
        return Message(message="Job posting extracted successfully")
    else:
        return Message(message="Job posting already extracted")
