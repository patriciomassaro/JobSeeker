from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session, text
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    JobPostingsPublic,
    JobPostingPublic,
    JobPostings,
    JobQueryParams,
    Message,
    ModelParameters,
)
from app.llm.job_description_extractor import JobDescriptionLLMExtractor

router = APIRouter()


@router.get("/", response_model=JobPostingsPublic)
def get_institutions(
    session: SessionDep, current_user: CurrentUser, params: JobQueryParams = Depends()
):
    filters = []
    query_params = {"limit": params.limit, "skip": params.skip}
    title_similarity = "1"
    company_similarity = "1"

    if params.job_title:
        title_similarity = "similarity(jp.title::text, :job_title)"
        query_params["job_title"] = params.job_title  # type:ignore

    if params.company_name:
        company_similarity = "similarity(jp.company::text, :company_name)"
        query_params["company_name"] = params.company_name  # type:ignore

    filter_query = " AND ".join(filters)
    query = text(
        f"""
            SELECT 
                jp.id,
                jp.title,
                jp.company,
                jp.company_url,
                jp.location,
                jp.description,
                sl.description AS seniority_level,
                et.description AS employment_type,
                el.description AS experience_level,
                rm.description AS remote_modality,
                srf.description AS salary_range,
                jp.industries,
                jp.job_functions,
                jp.skills,
                jp.job_salary_min,
                jp.job_salary_max,
                jp.job_poster_name,
                jp.job_poster_profile,
                jp.summary,
                ins.about AS institution_about,
                ins.website AS institution_website,
                ins.industry AS institution_industry,
                isz.description AS institution_size,
                ins.followers AS institution_followers,
                ins.employees AS institution_employees,
                ins.tagline AS institution_tagline,
                ins.location AS institution_location,
                ins.specialties AS institution_specialties,
                ({title_similarity} * {company_similarity}) AS combined_similarity

            FROM job_postings jp
            LEFT JOIN institutions ins ON jp.company_url = ins.url
            LEFT JOIN seniority_levels sl ON jp.seniority_level_id = sl.id
            LEFT JOIN employment_types et ON jp.employment_type_id = et.id
            LEFT JOIN experience_levels el ON jp.experience_level_id = el.id
            LEFT JOIN remote_modalities rm ON jp.remote_modality_id = rm.id
            LEFT JOIN salary_range_filters srf ON jp.salary_range_id = srf.id
            LEFT JOIN institution_sizes isz ON ins.size_id = isz.id
            ORDER BY combined_similarity DESC

            LIMIT :limit
            OFFSET :skip
            """
    )

    results = session.execute(query, query_params).fetchall()

    public_institutions = [JobPostingPublic(**dict(row._mapping)) for row in results]

    return JobPostingsPublic(data=public_institutions)


@router.post("/extract", response_model=Message)
def extract_job_postings(
    session: SessionDep,
    current_user: CurrentUser,
    job_posting_id: int,
    model_in: ModelParameters,
):
    if not current_user:
        return HTTPException(status_code=404, detail="User not found")

    statement = select(JobPostings).where(JobPostings.id == job_posting_id)
    job_posting = session.exec(statement).one_or_none()
    if job_posting is None:
        return HTTPException(status_code=404, detail="Job posting not found")
    if not job_posting.summary:
        extractor = JobDescriptionLLMExtractor(
            model_name=model_in.get_value(), temperature=model_in.temperature
        )
        extractor.extract_job_posting_and_write_to_db(job_id=job_posting_id)
        return Message(message="Job posting extracted successfully")
    else:
        return Message(message="Job posting already extracted")
