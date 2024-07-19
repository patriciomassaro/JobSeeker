import json
from sqlmodel import Session, select, col
from app.core.db import engine
from app.llm.base_extractor import BaseLLMExtractor
from app.crud.job_postings import get_job_posting_complete_by_id, get_job_posting_by_id
from app.models import (
    JobPostings,
    Institutions,
    LLMTransactionTypesEnum,
)
from app.llm.utils import get_columns
from pydantic import BaseModel, Field


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
    skills: list[str] | None = Field(
        description="List of essential skills for the job like technologies or programming languages. This includes soft skills"
    )
    education: str | None = Field(
        None, description="Minimum educational qualification required for the job."
    )


class JobDescription(BaseModel):
    title: str = Field(description="Job title for the position.")
    location: str | None = Field(
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


class JobDescriptionLLMExtractor(BaseLLMExtractor):
    def __init__(
        self,
        user_id: int,
        model_name: str,
        temperature: float = 0,
        log_file_name="llm.log",
        log_prefix="JobDescriptionExtractor",
    ):
        super().__init__(
            model_name=model_name,
            pydantic_object=JobPosting,  # type: ignore
            temperature=temperature,
            log_prefix=log_prefix,
            log_file_name=log_file_name,
            user_id=user_id,
        )

    def get_job_data_from_db(self, job_posting_id: int):
        with Session(engine) as session:
            job_posting_columns = get_columns(
                JobPostings,
                [
                    "title",
                    "description",
                    "company",
                    "company_url",
                    "industries",
                    "job_functions",
                    "job_salary_min",
                    "job_salary_max",
                    "skills",
                ],
            )

            institution_columns = get_columns(
                Institutions,
                [
                    "about",
                    "industry",
                    "specialties",
                    "followers",
                    "employees",
                    "tagline",
                ],
            )
            job_posting = get_job_posting_complete_by_id(
                session, job_posting_id, job_posting_columns, institution_columns
            )

            return json.dumps(job_posting._asdict())

    def extract_job_posting_and_write_to_db(self, job_posting_id: int):
        self.logger.info(f"Extracting job posting {job_posting_id}...")
        with Session(engine) as session:
            job_posting = get_job_posting_by_id(session, job_posting_id)
            if not job_posting.summary:
                job_data = self.get_job_data_from_db(job_posting_id)
                job_posting_summary, transaction_summary = self.extract_data_from_text(
                    text=job_data,
                    task_type=LLMTransactionTypesEnum.JOB_POSTING_EXTRACTION,
                    job_posting_id=job_posting_id,
                )
                job_posting.summary = job_posting_summary

                session.add(job_posting)
                session.commit()

                self.logger.info(f"Job posting {job_posting_id} updated successfully.")
            else:
                self.logger.info(
                    f"Job posting {job_posting_id} already exists in the database."
                )
