import os
from sqlmodel import Session, select
from sqlalchemy import desc, asc

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.callbacks import get_openai_callback
import random

from app.core.db import engine

from app.llm import ModelNames
from app.llm.base_builder import BaseBuilder
from app.logger import Logger
from app.models import (
    UserJobPostingComparisons,
    WorkExperiences,
    Users,
    WorkExperienceExamples,
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


WORK_EXPERIENCE_LATEX_TEMPLATE = """
    \cventry{{{START_DATE}-{END_DATE}}}
        {{{TITLE}}}
        {{{COMPANY}}}
        {{}}
        {{}}
        {{{ACCOMPLISHMENTS}}}
"""

EDUCATION_LATEX_TEMPLATE = """
    \cventry{{{START_DATE}-{END_DATE}}}
        {{{DEGREE}}}
        {{{INSTITUTION}}}
        {{}}
        {{}}
        {{{ACCOMPLISHMENTS}}}
"""

LANGUAGE_LATEX_TEMPLATE = """
    \cvline{{{LANGUAGE}}}{{{PROFICIENCY}}}
    """

SKILLS_LATEX_TEMPLATE = """
    \section{{Skills}}
    \cvline{{}}{{{SKILLS}}}
    """

CV_PROMPT_TEMPLATE = """
{{
    "context": {{
        "role": "Career Advisor",
        "task": "Tailor the resume to match a specific job posting",
        "goal": "Enable the client to highlight relevant experiences and skills using keywords that optimize visibility to applicant tracking systems."
    }},
    "inputs": {{
        "job_posting_data": "{job_posting_data}",
        "candidate_work_experience": "{parsed_work_experience}",
        "candidate_skills": "{parsed_skills}",
    }},
    "examples": {{
        "Explanation": "You will see how you answered in the past, and how the user corrected it. Use these examples to guide your edits but do not copy them directly.",
        "examples": {examples}
    }}
    "guidelines": {{
        "format": "Adhere to these formatting rules: {format_requirements}",
        "Preambles": "DO NOT OUTPUT ANYTHING ELSE THAN THE JSON OBJECT",
        "content": {{
            "adapt_titles": "Modify job titles to reflect those in the job posting.",
            "description_style": "Describe responsibilities and achievements using the STAR method.",
            "avoid_adjectives": "Exclude adjectives and adverbs in descriptions.",
            "focus_relevance": "Emphasize skills and experiences directly relevant to the job."
        }}
    }},
    "constraints": {{
        "experience_inclusion": "Include all work experiences.",
        "consistent_tense": "Use a consistent verb tense throughout the resume.",
        "excluded_words": ["Spearhead", "Pioneer", "Advanced"],
        "max_words_per_achievement": "Limit each achievement to 30 words."
    }}
}}
"""


class CVBuilder(BaseBuilder):
    def __init__(
        self,
        model_name: str,
        user_id: int,
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
        )
        self.examples = self._get_examples_from_db()
        self.output_parser = JsonOutputParser(pydantic_object=WorkExperiencesLLM)
        self._create_chain()
        print("CV Builder instantiated")

    def _get_examples_from_db(self):
        examples_list = []
        with Session(engine) as session:
            comparison_ids = session.exec(
                select(UserJobPostingComparisons.id).where(
                    UserJobPostingComparisons.user_id == self.user_id
                )
            ).all()
            comparison_ids = list(comparison_ids)

            examples = session.exec(
                select(WorkExperienceExamples).where(
                    WorkExperienceExamples.comparison_id.in_(comparison_ids)
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

    def _load_latex_to_string(self) -> str:
        with open(
            os.path.join(ROOT_DIR, "media", f"{self.user_id}", "CV.tex"), "r"
        ) as file:
            return file.read()

    def _load_template_to_string(self) -> str:
        with open(os.path.join(ROOT_DIR, "templates", "CV.tex"), "r") as file:
            return file.read()

    def _create_chain(self):
        self.template = PromptTemplate(
            template=CV_PROMPT_TEMPLATE,
            input_variables=[
                "job_posting_data",
            ],
            partial_variables={
                "parsed_work_experience": self._get_user_attribute(
                    "parsed_work_experiences"
                ),
                "parsed_skills": self._get_user_attribute("parsed_skills"),
                "format_requirements": self.output_parser.get_format_instructions(),
                "examples": self.examples,
            },
        )
        self.chain = self.template | self.llm | self.output_parser

    def _run_chain(self, job_id: int):
        print("Running chain")
        with get_openai_callback() as cb:
            result = self.chain.invoke(
                {
                    "job_posting_data": self._get_job_summary(job_id=job_id),
                    # "requirement_qualification_comparison":self._get_comparison_summary(job_id=job_id)
                }
            )
            self.logger.info(f"Built CV for user {self.user_id} and {job_id} \n {cb}")
            return result

    def _save_cv_to_database(self, job_id: int, pdf_bytes: bytes):
        with Session(engine) as session:
            comparison = session.exec(
                select(UserJobPostingComparisons).where(
                    UserJobPostingComparisons.job_posting_id == job_id,
                    UserJobPostingComparisons.user_id == self.user_id,
                )
            ).first()
            if comparison:
                comparison.resume = pdf_bytes
                session.commit()
            else:
                self.logger.error("Comparison not found in database.")

    def _save_work_experiences_to_database(
        self, job_id: int, custom_work_experiences: list[WorkExperiences]
    ):
        with Session(engine) as session:
            comparison = session.exec(
                select(UserJobPostingComparisons).where(
                    UserJobPostingComparisons.job_posting_id == job_id,
                    UserJobPostingComparisons.user_id == self.user_id,
                )
            ).one_or_none()

            if not comparison:
                raise ValueError("Comparison not found in database.")

            session.query(WorkExperiences).filter_by(
                comparison_id=comparison.id
            ).delete()
            for work_experience in custom_work_experiences:
                work_experience_paragraph = WorkExperiences(
                    comparison_id=comparison.id,
                    start_date=work_experience.get("start_date", ""),
                    end_date=work_experience.get("end_date", ""),
                    company=work_experience.get("company_name", ""),
                    title=work_experience.get("title", ""),
                    accomplishments=work_experience.get("accomplishments", []),
                )
                session.add(work_experience_paragraph)
            session.commit()

    def _load_personal_data_to_cv(self, template: str) -> str:
        with Session(engine) as session:
            user = session.exec(select(Users).where(Users.id == self.user_id)).first()

            if user and user.parsed_personal:
                personal_data = user.parsed_personal
                template = template.replace(
                    "FIRSTNAME", personal_data.get("first_name", "")
                )
                template = template.replace(
                    "LASTNAME", personal_data.get("last_name", "")
                )
                template = template.replace("MAIL", personal_data.get("email", ""))
                template = template.replace(
                    "PHONE", personal_data.get("contact_number", "")
                )
                template = template.replace(
                    "LOCATION", personal_data.get("location", "")
                )

                personal_links_string = ""
                for personal_link in personal_data.get("personal_links", []):
                    if "linkedin" in personal_link:
                        personal_links_string += (
                            f"\\social[linkedin][{personal_link}]{{{personal_link}}}\n"
                        )
                    elif "github" in personal_link:
                        personal_links_string += (
                            f"\\social[github][{personal_link}]{{{personal_link}}}\n"
                        )
                template = template.replace("SOCIAL", personal_links_string)
        return template

    def _add_education_to_cv(self, template: str) -> str:
        with Session(engine) as session:
            education_string = "\\section{Education}"
            user = session.exec(select(Users).where(Users.id == self.user_id)).first()
            if user and user.parsed_educations:
                # sort by start date desc
                education_data = user.parsed_educations
                education_data = sorted(
                    education_data, key=lambda x: x.get("start_date", ""), reverse=True
                )
                for education in education_data:
                    if education.get("accomplishments", None):
                        accomplishments_string = "\\begin{itemize} FILL \\end{itemize}"
                        accomplishment_items = ""
                        for accomplishment in education.get("accomplishments", []):
                            accomplishment_items += (
                                f"\\item {self._escape_latex(accomplishment)} \n"
                            )
                        accomplishments_string = accomplishments_string.replace(
                            "FILL", accomplishment_items
                        )
                    else:
                        accomplishments_string = ""

                    education_string += EDUCATION_LATEX_TEMPLATE.format(
                        START_DATE=education.get("start_date", ""),
                        END_DATE=education.get("end_date", ""),
                        DEGREE=education.get("degree", ""),
                        INSTITUTION=education.get("institution", ""),
                        ACCOMPLISHMENTS=accomplishments_string,
                    ).replace("-None", "")
            return template.replace("EDUCATIONS", education_string)

    def _add_work_experiences_to_cv(self, template: str, comparison_id: int) -> str:
        with Session(engine) as session:
            statement = (
                select(WorkExperiences)
                .where(WorkExperiences.comparison_id == comparison_id)
                .order_by(
                    desc(WorkExperiences.end_date), asc(WorkExperiences.start_date)
                )
            )
            work_experiences = session.exec(statement).all()
            if work_experiences:
                work_experience_string = "\\section{Work Experience}"
                for work_experience in work_experiences:
                    if work_experience.accomplishments:
                        accomplishments_string = "\\begin{itemize} FILL \\end{itemize}"
                        accomplishment_items = ""
                        for accomplishment in work_experience.accomplishments:
                            accomplishment_items += (
                                f"\\item {self._escape_latex(accomplishment)} \n"
                            )
                        accomplishments_string = accomplishments_string.replace(
                            "FILL", accomplishment_items
                        )
                    else:
                        accomplishments_string = ""
                    work_experience_string += WORK_EXPERIENCE_LATEX_TEMPLATE.format(
                        START_DATE=work_experience.start_date,
                        END_DATE=work_experience.end_date,
                        TITLE=work_experience.title,
                        COMPANY=work_experience.company,
                        ACCOMPLISHMENTS=accomplishments_string,
                    )
            else:
                work_experience_string = ""
            return template.replace("WORKEXPERIENCES", work_experience_string)

    def _add_languages_to_cv(self, template: str) -> str:
        with Session(engine) as session:
            language_string = "\section{Languages}"
            user = session.exec(select(Users).where(Users.id == self.user_id)).first()

            if user and user.parsed_languages:
                language_data = user.parsed_languages
                for language in language_data:
                    language_string += LANGUAGE_LATEX_TEMPLATE.format(
                        LANGUAGE=language.get("language", ""),
                        PROFICIENCY=language.get("proficiency", ""),
                    )
        return template.replace("LANGUAGES", language_string)

    def _add_skills_to_cv(self, template: str) -> str:
        with Session(engine) as session:
            skills_string = ""
            user = session.exec(select(Users).where(Users.id == self.user_id)).first()
            if user and user.parsed_skills:
                skills_data = user.parsed_skills
                skills_string = SKILLS_LATEX_TEMPLATE.format(
                    SKILLS=", ".join(skills_data)
                )
        return template.replace("SKILLS", skills_string)

    def _generate_tailored_cv(self, job_id: int):
        # get the comparison
        with Session(engine) as session:
            comparison = (
                session.query(UserJobPostingComparisons)
                .filter_by(job_posting_id=job_id, user_id=self.user_id)
                .first()
            )
            if comparison:
                latex = self._load_template_to_string()
                latex = self._load_personal_data_to_cv(template=latex)
                latex = self._add_work_experiences_to_cv(
                    latex, comparison_id=comparison.id
                )
                latex = self._add_education_to_cv(latex)
                latex = self._add_languages_to_cv(latex)
                latex = self._add_skills_to_cv(latex)
                return latex
            else:
                self.logger.error("Comparison not found in database.")

    def _build(self, job_id: int, use_llm=True):
        self.logger.info(f"Building CV for user {self.user_id} and Job {job_id}")
        if use_llm:
            custom_work_experiences = self._run_chain(job_id=job_id)
            custom_work_experiences = custom_work_experiences["work_experiences"]
            self._save_work_experiences_to_database(
                job_id=job_id, custom_work_experiences=custom_work_experiences
            )
        custom_cv_latex = self._generate_tailored_cv(job_id=job_id)

        pdf_bytes = self._create_pdf_from_latex(
            latex_string=custom_cv_latex,
            path=os.path.join(
                ROOT_DIR,
                "media",
                f"{self.user_id}",
                f"{self._get_job_company_and_position(job_id)}_CV",
            ),
        )
        self._save_cv_to_database(job_id=job_id, pdf_bytes=pdf_bytes)
        self._cleanup_build_directory(
            os.path.join(ROOT_DIR, "media", f"{self.user_id}")
        )
