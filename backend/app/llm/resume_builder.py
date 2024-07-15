import os
from typing import Any
from sqlmodel import Session, select, desc, asc

from app.core.db import engine
from app.models import Users, WorkExperiences, Comparisons
from app.llm.base_builder import BasePDFBuilder

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(ROOT_PATH, "templates", "resume_template.tex")


class ResumeBuilder(BasePDFBuilder):
    def __init__(self, user_id: int, comparison_id: int):
        super().__init__()
        self.user_id = user_id
        self.comparison_id = comparison_id
        self.template_path = TEMPLATE_PATH

    def _get_user_data(self) -> dict[str, Any]:
        with Session(engine) as session:
            user = session.exec(select(Users).where(Users.id == self.user_id)).one()
            return {
                "personal": user.parsed_personal,
                "skills": user.parsed_skills,
                "languages": user.parsed_languages,
                "educations": user.parsed_educations,
            }

    def _get_work_experiences(self) -> list[dict[str, Any]]:
        with Session(engine) as session:
            work_experiences = session.exec(
                select(WorkExperiences)
                .where(WorkExperiences.comparison_id == self.comparison_id)
                .order_by(
                    desc(WorkExperiences.end_date), asc(WorkExperiences.start_date)
                )
            ).all()
            return [we.model_dump() for we in work_experiences]

    def _format_work_experience(self, experiences: list[dict[str, Any]]) -> str:
        formatted_experiences = [r"\section{Work Experience}"]
        for exp in experiences:
            exp_str = (
                rf"\cventry{{{exp['start_date']}--{exp.get('end_date', 'Present')}}}"
                rf"{{{exp['title']}}}"
                rf"{{{exp['company']}}}"
                r"{}{}"
            )
            if exp.get("accomplishments"):
                exp_str += r"{\begin{itemize}"
                for acc in exp["accomplishments"]:
                    exp_str += rf"\item {self._escape_latex(acc)}"
                exp_str += r"\end{itemize}}"
            else:
                exp_str += "{}"
            formatted_experiences.append(exp_str)
        return "\n".join(formatted_experiences)

    def _format_education(self, educations: list[dict[str, Any]]) -> str:
        formatted_educations = [r"\section{Education}"]
        for edu in sorted(
            educations, key=lambda x: x.get("start_date", ""), reverse=True
        ):
            edu_str = (
                rf"\cventry{{{edu['start_date']}--{edu.get('end_date', 'Present')}}}"
                rf"{{{edu['degree']}}}"
                rf"{{{edu['institution']}}}"
                r"{}{}"
            )
            if edu.get("accomplishments"):
                edu_str += r"{\begin{itemize}"
                for acc in edu["accomplishments"]:
                    edu_str += rf"\item {acc}"
                edu_str += r"\end{itemize}}"
            else:
                edu_str += "{}"
            formatted_educations.append(edu_str)
        return "\n".join(formatted_educations)

    def _format_skills(self, skills: list[str]) -> str:
        return rf"\section{{Skills}}\n\cvline{{}}{{{', '.join(skills)}}}"

    def _format_languages(self, languages: list[dict[str, str]]) -> str:
        formatted_languages = [r"\section{Languages}"]
        for lang in languages:
            formatted_languages.append(
                rf"\cvline{{{lang['language']}}}{{{lang['proficiency']}}}"
            )
        return "\n".join(formatted_languages)

    def _format_social_links(self, personal_links: list[str]) -> str:
        formatted_links = []
        for link in personal_links:
            if "linkedin" in link.lower():
                formatted_links.append(rf"\social[linkedin][{link}]{{{link}}}")
            elif "github" in link.lower():
                formatted_links.append(rf"\social[github][{link}]{{{link}}}")
        return "\n".join(formatted_links)

    def build_resume(self) -> bytes:
        # 1. Load the template
        latex_template = self._load_template(self.template_path)

        # 2. Get and format all the data
        user_data = self._get_user_data()
        work_experiences = self._get_work_experiences()

        # 3. Replace placeholders in the template with formatted content
        replacements = {
            "FIRSTNAME": user_data["personal"].get("first_name", ""),
            "LASTNAME": user_data["personal"].get("last_name", ""),
            "PHONE": user_data["personal"].get("contact_number", ""),
            "MAIL": user_data["personal"].get("email", ""),
            "LOCATION": user_data["personal"].get("location", ""),
            "SOCIAL": self._format_social_links(
                user_data["personal"].get("personal_links", [])
            ),
            "WORKEXPERIENCES": self._format_work_experience(work_experiences),
            "EDUCATIONS": self._format_education(user_data["educations"]),
            "SKILLS": self._format_skills(user_data.get("skills", [])),
            "LANGUAGES": self._format_languages(user_data.get("languages", [])),
        }

        filled_latex = self._replace_placeholders(latex_template, replacements)

        # 4. Generate PDF
        output_path = os.path.join(ROOT_PATH, "media", f"resume_{self.comparison_id}")
        pdf_bytes = self.generate_pdf(
            latex_content=filled_latex, output_path=output_path
        )

        # 5. Save to database
        self._save_resume_to_database(pdf_bytes)

        return pdf_bytes

    def _save_resume_to_database(self, pdf_bytes: bytes):
        with Session(engine) as session:
            comparison = session.exec(
                select(Comparisons).where(Comparisons.id == self.comparison_id)
            ).first()
            if comparison:
                comparison.resume = pdf_bytes
                session.add(comparison)
                session.commit()
            else:
                raise ValueError("Comparison not found in database.")
