import os
from typing import Any
from sqlmodel import Session, select, desc, case
import datetime

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

    @staticmethod
    def _date_key(year: int | None, month: int | None) -> tuple[int, int]:
        """Create a sortable key from year and month."""
        return (year or 9999, month or 12)  # Use 9999 for year and 12 for month if None

    @staticmethod
    def _format_date(year: int, month: int | None) -> str:
        """Format year and month into a string."""
        if month:
            return datetime.date(year, month, 1).strftime("%b %Y")
        return str(year)

    def _get_work_experiences(self):
        with Session(engine) as session:
            query = (
                select(WorkExperiences)
                .where(WorkExperiences.comparison_id == self.comparison_id)
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

            return list(session.exec(query).all())

    def _get_user_data(self) -> dict[str, Any]:
        with Session(engine) as session:
            user = session.exec(select(Users).where(Users.id == self.user_id)).one()
            return {
                "personal": user.parsed_personal,
                "skills": user.parsed_skills,
                "languages": user.parsed_languages,
                "educations": user.parsed_educations,
            }

    def _format_work_experience(self, experiences: list[WorkExperiences]) -> str:
        formatted_experiences = [r"\section{Work Experience}"]
        for exp in experiences:
            start_date = self._format_date(exp.start_year, exp.start_month)
            end_date = (
                self._format_date(exp.end_year, exp.end_month)
                if exp.end_year
                else "Present"
            )

            exp_str = (
                r"\begin{twocolentry}"
                rf"{{{start_date}--{end_date}}}"
                rf"\textbf{{{exp.title}}}, {exp.company}"
                r"\end{twocolentry}"
            )
            if exp.accomplishments:
                exp_str += "\\vspace{0.10cm}\n"
                exp_str += "\\begin{onecolentry}\n"
                exp_str += "\\begin{highlights}\n"
                for acc in exp.accomplishments:
                    exp_str += rf"\item {self._escape_latex(acc)} "
                exp_str += "\\end{highlights}\n"
                exp_str += "\\end{onecolentry}\n"
                exp_str += "\\vspace{0.35cm}\n"
            formatted_experiences.append(exp_str)
        return "\n".join(formatted_experiences)

    def _format_education(self, educations: list[dict[str, Any]]) -> str:
        formatted_educations = [r"\section{Education}"]
        for edu in sorted(
            educations,
            key=lambda x: self._date_key(x.get("end_year"), x.get("end_month")),
            reverse=True,
        ):
            start_date = self._format_date(edu["start_year"], edu.get("start_month"))
            end_date = (
                self._format_date(edu["end_year"], edu.get("end_month"))
                if edu.get("end_year")
                else "Present"
            )

            edu_str = (
                "\\begin{twocolentry} \n"
                rf"{{{start_date}--{end_date}}}"
                rf"\textbf{{{edu['degree']}}}, {edu['institution']}"
                "\\end{twocolentry} \n"
            )
            if edu.get("accomplishments"):
                edu_str += "\\vspace{0.10cm}\n"
                edu_str += "\\begin{onecolentry}\n"
                edu_str += "\\begin{highlights}\n"
                for acc in edu["accomplishments"]:
                    edu_str += rf"\item {self._escape_latex(acc)} "
                edu_str += "\\end{highlights} \n"
                edu_str += "\\end{onecolentry}\n"
            edu_str += "\\vspace{0.35cm} \n"
            formatted_educations.append(edu_str)
        return "\n".join(formatted_educations)

    def _format_skills(self, skills: list[str]) -> str:
        if not skills:
            return ""

        return (
            "\\section{Skills} \n"
            "\\begin{onecolentry}\n"
            rf"{', '.join(skills)}"
            "\\end{onecolentry}\n"
            "\\vspace{0.35cm}\n"
        )

    def _format_languages(self, languages: list[dict[str, str]]) -> str:
        if not languages:
            return ""
        formatted_languages = [r"\section{Languages}"]
        for lang in languages:
            formatted_languages.append(
                rf"\begin{{onecolentry}} \textbf{{{lang['language']}}}, {lang['proficiency']} \end{{onecolentry}}"
            )
        return " ".join(formatted_languages)

    def _format_personal_info(self, personal_info: list[str]) -> str:
        formatted_info_list = [
            rf"\mbox{{{self._escape_latex(text)}}} "
            for text in personal_info
            if text != ""
        ]
        return "\n \\kern 5.0pt \\AND \\kern 5.0 pt".join(formatted_info_list)

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
            "PERSONALINFO": self._format_personal_info(
                [
                    user_data["personal"].get("location", ""),
                    user_data["personal"].get("email", ""),
                    user_data["personal"].get("contact_number", ""),
                    *user_data["personal"].get("personal_links", []),
                ]
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
