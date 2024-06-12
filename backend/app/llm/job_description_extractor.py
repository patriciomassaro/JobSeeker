import json
import re
from sqlmodel import Session
from app.core.db import engine
from app.llm.base_extractor import BaseLLMExtractor
from app.llm import ModelNames
from app.models import (
    JobPostings,
    Institutions,
    InstitutionSizes,
    EmploymentTypes,
    SeniorityLevels,
)
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor, as_completed


class Responsibilities(BaseModel):
    items: list[str] = Field(description="List of key job responsibilities.")


class Qualifications(BaseModel):
    experience_years: None | int = Field(
        None, description="Required years of experience."
    )
    must_have: list[str] | None = Field(
        None, description="List of must-have qualifications/experiences for the job"
    )
    nice_to_have: list[str] | None = Field(
        None,
        description="List of optional or nice to have qualifications/experiences for the job.",
    )
    skills: list[str] = Field(
        description="List of essential skills for the job like technologies or programming languages. This includes soft skills"
    )
    education: str | None = Field(
        None, description="Minimum educational qualification required for the job."
    )


class JobDescription(BaseModel):
    title: str = Field(description="Job title for the position.")
    location: str = Field(
        description="Geographical location or 'Remote' if applicable."
    )
    involved_team: str | None = Field(
        None, description="Name of the team the job role is part of"
    )
    seniority_level: str | None = Field(
        None, description="Seniority level of the job role."
    )
    looking_for: str | None = Field(
        None,
        description="what is the company looking for. Example: The team is looking for talented ML engineers to help build the next generation of AI products.",
    )
    what_the_candidate_will_do: str | None = Field(
        None,
        description="brief description of the candidate duties. Example: you will work with public data and diverse teams to build novel AI products.",
    )
    responsibilities: Responsibilities = Field(
        description="Specific responsibilities associated with the job."
    )
    qualifications: Qualifications = Field(
        description="Qualifications and skills required for the job."
    )


class CompanyProfile(BaseModel):
    name: str = Field(description="Name of the company.")
    industry: str | None = Field(
        None, description="Industry sector the company operates in."
    )
    size: str | None = Field(
        None, description="Number of employees or scale of operations."
    )
    description: str | None = Field(
        None, description="Brief description of the company."
    )
    values: list[str] | None = Field(None, description="Core values of the company.")
    culture: str | None = Field(None, description="Overview of the company culture.")
    headquarters: str | None = Field(
        None, description="Location of the company's headquarters."
    )
    website: str | None = Field(None, description="Website URL of the company.")
    mission_statement: str | None = Field(
        None, description="The company's mission statement."
    )
    about: list[str] | None = Field(
        None,
        description="Detailed information about the company. Including history, random facts, etc.",
    )


class JobPosting(BaseModel):
    job_description: JobDescription = Field(
        description="General information about the job posting."
    )
    company_profile: CompanyProfile = Field(
        description="Information about the company offering the job."
    )


# Validator example within a class, to ensure pay ranges are provided correctly


class JobDescriptionLLMExtractor(BaseLLMExtractor):
    def __init__(
        self,
        model_name: ModelNames,
        temperature: float = 0,
        log_file_name="llm.log",
        log_prefix="JobDescriptionExtractor",
    ):
        super().__init__(
            model_name=model_name.value,
            pydantic_object=JobPosting,  # type: ignore
            temperature=temperature,
            log_prefix=log_prefix,
            log_file_name=log_file_name,
        )

    def get_job_data_from_text(self, job_posting_id: int):
        with Session(engine) as session:
            job_posting_columns = [
                getattr(JobPostings, attr)
                for attr in JobPostings.__table__.columns.keys()
                if attr
                in [
                    "title",
                    "seniority_level",  # NOt the ID, but the description after joining
                    "employment_type",  # NOt the ID, but the description after joining
                    "description",
                    "company",
                    "company_url",
                    "industries",
                    "job_functions",
                    "job_salary_min",
                    "job_salary_max",
                    "skills",
                ]
            ]
            institution_columns = [
                getattr(Institutions, attr)
                for attr in Institutions.__table__.columns.keys()
                if attr
                in [
                    "about",
                    "industry",
                    "specialties",
                    "followers",
                    "employees",
                    "tagline",
                ]
            ]
            institution_sizes_columns = [
                getattr(InstitutionSizes, attr)
                for attr in InstitutionSizes.__table__.columns.keys()
                if attr in ["description"]
            ]
            employment_type_columns = [
                getattr(EmploymentTypes, attr)
                for attr in EmploymentTypes.__table__.columns.keys()
                if attr in ["description"]
            ]
            seniority_level_columns = [
                getattr(SeniorityLevels, attr)
                for attr in SeniorityLevels.__table__.columns.keys()
                if attr in ["description"]
            ]

            job_posting = (
                session.query(
                    *job_posting_columns,
                    *institution_columns,
                    *institution_sizes_columns,
                    *employment_type_columns,
                    *seniority_level_columns,
                )
                .outerjoin(
                    Institutions,
                    JobPostings.company_url == Institutions.url,
                )
                .outerjoin(InstitutionSizes, Institutions.size == InstitutionSizes.id)
                .outerjoin(
                    SeniorityLevels, JobPostings.seniority_level == SeniorityLevels.id
                )
                .outerjoin(
                    EmploymentTypes, JobPostings.employment_type == EmploymentTypes.id
                )
                .filter(JobPostings.id == job_posting_id)
                .first()
            )
            if job_posting:
                return json.dumps(job_posting._asdict())
            else:
                raise ValueError(
                    f"Job posting {job_posting_id} not found in the database."
                )

    def extract_job_posting_and_write_to_db(self, job_id: int, replace_existing: bool):
        self.logger.info(f"Extracting job posting {job_id}...")
        with Session(engine) as session:
            job_posting_record = (
                session.query(JobPostings).filter(JobPostings.id == job_id).first()
            )
            if job_posting_record:
                if replace_existing or job_posting_record.job_posting_summary is None:
                    job_posting = self.get_job_data_from_text(job_id)
                    job_description_extraction = self.extract_data_from_text(
                        text=job_posting
                    )
                    job_posting_record.job_posting_summary = job_description_extraction
                    session.commit()
                    self.logger.info(f"Job posting {job_id} updated successfully.")
                    return 1
                else:
                    self.logger.info(
                        f"Job posting {job_id} already exists in the database."
                    )
                    return 0

    # Using ThreadPoolExecutor to parallelize the update process
    def update_job_postings(self, job_ids: list[int], replace_existing: bool = False):
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submitting tasks to the executor
            future_to_job_posting = {
                executor.submit(
                    self.extract_job_posting_and_write_to_db, job_id, replace_existing
                ): job_id
                for job_id in job_ids
            }
            for future in as_completed(future_to_job_posting):
                job_posting = future_to_job_posting[future]
                try:
                    result = future.result()
                except Exception as exc:
                    self.logger.error(
                        f"Job posting {job_ids} generated an exception: {exc}"
                    )


if __name__ == "__main__":
    job_description_extractor = JobDescriptionLLMExtractor(
        model_name=ModelNames.GPT3_TURBO, temperature=0
    )
    ids = [3872263836]
    job_description_data = job_description_extractor.update_job_postings(ids)
