import os
from sqlmodel import Session, select

import random

from app.core.db import engine

from app.llm.base_generator import BaseGenerator
from app.models import (
    Comparisons,
    WorkExperiences,
    WorkExperienceExamples,
    LLMTransactionTypesEnum,
)
from pydantic import BaseModel, Field

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WorkExperienceLLM(BaseModel):
    title: str = Field(description="Title of the position held.")
    company_name: str = Field(
        description="Name of the company where the position was held."
    )
    start_date: str = Field(
        description="Start date of the employment in YYYY-MM format."
    )
    end_date: str | None = Field(
        None, description="End date of the employment in YYYY-MM format, if applicable."
    )
    accomplishments: list[str] = Field(
        description="List of achievements or responsibilities in the position."
    )


class WorkExperiencesLLM(BaseModel):
    work_experiences: list[WorkExperienceLLM] = Field(
        description="List of work experiences."
    )


CV_PROMPT_TEMPLATE = r"""
{{
    "context": {{
        "role": "Career Advisor",
        "task": "Tailor the work experiences of a candidate to match a specific job posting",
        "goal": "Enable the client to highlight relevant experiences and skills using keywords that optimize visibility to applicant tracking systems."
    }},
    "examples": {{
        "Explanation": "Here are some previous responses from you, and how users corrected them in. Use them to guide your edits but do not copy the content directly.",
        "examples": {examples}
    }}
    "guidelines": {{
        "format": "the work experiences must adhere to the following structure : {format_requirements}",
        "Preambles": "DO NOT OUTPUT ANYTHING ELSE THAN THE JSON OBJECT",
        "content": {{
            "adapt_titles": "Modify job titles to reflect those in the job posting.",
            "description_style": "Describe responsibilities and achievements using the STAR method.",
            "avoid_adjectives": "Exclude adjectives and adverbs in descriptions.",
            "focus_relevance": "Emphasize skills and experiences directly relevant to the job."
        }}
    }},
    "constraints": {{
        "experience_inclusion": "Include all work experiences from the user",
        "consistent_tense": "Use a consistent verb tense throughout all work experiences.",
        "excluded_words": ["Spearhead", "Pioneer", "Advanced"],
        "max_words_per_achievement": "Limit each achievement to 25 words."
    }}
}}
"""

USER_PROMPT_TEMPLATE = r"""
    "inputs": {{
        "job_posting_data": "{job_posting_data}",
        "candidate_work_experience": "{parsed_work_experience}",
        "candidate_skills": "{parsed_skills}",
    }},
"""


class WorkExperienceGenerator(BaseGenerator):
    def __init__(
        self,
        model_name: str,
        user_id: int,
        job_posting_id: int,
        comparison_id: int,
        temperature: float = 0,
        log_file_name="llm.log",
        log_prefix="CVBuilder",
    ):
        super().__init__(
            model_name=model_name,
            user_id=user_id,
            temperature=temperature,
            log_file_name=log_file_name,
            log_prefix=log_prefix,
            job_posting_id=job_posting_id,
            comparison_id=comparison_id,
        )
        self.system_prompt_template = CV_PROMPT_TEMPLATE
        self.user_prompt_template = USER_PROMPT_TEMPLATE
        self.output_pydantic_model = WorkExperiencesLLM

    def _get_examples_from_db(self):
        examples_list = []
        with Session(engine) as session:
            comparison_ids = session.exec(
                select(Comparisons.id).where(Comparisons.user_id == self.user_id)
            ).all()
            comparison_ids = list(comparison_ids)

            examples = session.exec(
                select(WorkExperienceExamples).where(
                    WorkExperienceExamples.comparison_id.in_(comparison_ids)  # type: ignore
                )
            ).all()

            examples = random.sample(examples, min(10, len(examples)))

        for example in examples:
            examples_list.append(
                {
                    "original_title": example.original_title,
                    "edited_title": example.edited_title,
                    "original_accomplishments": example.original_accomplishments,
                    "edited_accomplishments": example.edited_accomplishments,
                }
            )
        return examples_list

    def _create_system_prompt(self) -> str:
        return self.system_prompt_template.format(
            examples=self._get_examples_from_db(),
            format_requirements=self.output_pydantic_model.model_json_schema(),
        )

    def _create_user_prompt(self) -> str:
        comparison_data = self._get_comparison_data()
        return self.user_prompt_template.format(
            job_posting_data=comparison_data["job_info"]["summary"],
            parsed_work_experience=comparison_data["user_attributes"][
                "work_experiences"
            ],
            parsed_skills=comparison_data["user_attributes"]["parsed_skills"],
        )

    def _save_work_experiences_to_database(self, new_work_experiences):
        with Session(engine) as session:
            comparison = session.exec(
                select(Comparisons).where(
                    Comparisons.job_posting_id == self.job_posting_id,
                    Comparisons.user_id == self.user_id,
                )
            ).one_or_none()

            if not comparison:
                raise ValueError("Comparison not found in database.")

            previous_work_experiences = session.exec(
                select(WorkExperiences).where(
                    WorkExperiences.comparison_id == comparison.id
                )
            ).all()
            for we in previous_work_experiences:
                session.delete(we)

            session.add_all(
                [
                    WorkExperiences(
                        comparison_id=comparison.id,
                        start_date=we.start_date,
                        end_date=we.end_date,
                        company=we.company_name,
                        title=we.title,
                        accomplishments=we.accomplishments,
                    )
                    for we in new_work_experiences
                ]
            )

            session.commit()

    def generate_work_experiences(self):
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt()

        work_experiences, _ = self._generate_and_parse_content(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_type=LLMTransactionTypesEnum.CV_GENERATION,
            pydantic_model=self.output_pydantic_model,
        )

        if isinstance(work_experiences, WorkExperiencesLLM):
            self._save_work_experiences_to_database(work_experiences.work_experiences)
        else:
            raise ValueError(
                f"Unexpected type for parsed_content: {type(work_experiences)}"
            )
