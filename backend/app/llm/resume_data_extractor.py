import re
import os
from sqlmodel import Session, select
from app.core.db import engine
from app.llm.base_extractor import BaseLLMExtractor
from app.logger import Logger
from app.llm.utils import extract_text_from_pdf_bytes
from app.models import Users, LLMTransactions, LLMTransactionTypesEnum
from pydantic import BaseModel, Field, validator

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Personal(BaseModel):
    first_name: str = Field(description="Full name of the individual.")
    last_name: str = Field(description="Last name of the individual.")
    contact_number: str | None = Field(None, description="Contact phone number.")
    email: str | None = Field(None, description="Email address.")
    summary: str | None = Field(
        None,
        description="Brief summary about the individual's professional background.",
    )
    location: str | None = Field(None, description="Location of the individual.")
    personal_links: list[str] | None = Field(
        None,
        description="List of personal or professional links like github,linkedin, etc.",
    )

    @validator("email")
    def email_validator(cls, v):
        if v is not None:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
                raise ValueError("Invalid email address")
        return v


class WorkExperience(BaseModel):
    title: str = Field(description="Title of the position held.")
    company_name: str = Field(
        description="Name of the company where the position was held."
    )
    start_date: str = Field(description="Start date of the employment in YYYY format.")
    end_date: str | None = Field(
        None, description="End date of the employment in YYYY-MM format, if applicable."
    )
    accomplishments: list[str] = Field(
        description="List of achievements or responsibilities in the position"
    )


class Education(BaseModel):
    degree: str = Field(description="Name of the degree obtained.")
    institution: str = Field(description="Name of the educational institution.")
    start_date: str = Field(
        description="Start date of the degree program in YYYY-MM format."
    )
    end_date: str | None = Field(
        None,
        description="End date of the degree program in YYYY-MM format, if applicable.",
    )
    accomplishments: list[str] | None = Field(
        None, description="List of achievements or responsibilities during studies."
    )


class Language(BaseModel):
    language: str = Field(description="Name of the language.")
    proficiency: str = Field(description="Level of proficiency in the language.")


class CV(BaseModel):
    personal: Personal = Field(description="Profile information of the individual.")
    work_experiences: list[WorkExperience] = Field(
        description="List of work experiences."
    )
    educations: list[Education] = Field(
        description="List of educational qualifications."
    )
    skills: list[str] = Field(description="List of any skills described in the CV.")
    languages: list[Language] | None = Field(
        None, description="List of languages spoken and proficiency levels."
    )


class ResumeLLMExtractor(BaseLLMExtractor):
    def __init__(
        self,
        model_name: str,
        user_id: int,
        temperature: float = 0,
        prefix="CVExtractor",
        log_file_name="llm.log",
    ):
        super().__init__(
            model_name=model_name,
            pydantic_object=CV,  # type: ignore
            temperature=temperature,
            user_id=user_id,
        )
        self.logger = Logger(prefix=prefix, log_file_name=log_file_name).get_logger()

    def extract_cv_and_write_to_db(self):
        self.logger.info(f"Extracting CV data for user {self.user_id}")
        with Session(engine) as session:
            user_record = session.exec(
                select(Users).where(Users.id == self.user_id)
            ).first()

            if user_record and user_record.resume:
                cv_text = extract_text_from_pdf_bytes(user_record.resume)
                resume_summary, transaction_summary = self.extract_data_from_text(
                    text=cv_text, task_type=LLMTransactionTypesEnum.USER_CV_EXTRACTION
                )

                # Update user record with extracted data
                user_record.parsed_personal = resume_summary.get("personal", {})
                user_record.parsed_work_experiences = resume_summary.get(
                    "work_experiences", {}
                )
                user_record.parsed_educations = resume_summary.get("educations", {})
                user_record.parsed_skills = resume_summary.get("skills", [])
                user_record.parsed_languages = resume_summary.get("languages", {})

                session.add(user_record)
                session.commit()

                self.logger.info(
                    f"Successfully extracted CV data for user {self.user_id}"
                )
                return 1
            else:
                self.logger.info(f"User {self.user_id} has no resume")
                return 0
