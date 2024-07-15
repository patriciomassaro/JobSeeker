import os
from typing import Any
from sqlmodel import Session, select

from app.core.db import engine
from app.models import Users, CoverLetterParagraphs, Comparisons
from app.llm.base_builder import BasePDFBuilder

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(ROOT_PATH, "templates", "cover_letter_template.tex")


class CoverLetterBuilder(BasePDFBuilder):
    def __init__(self, user_id: int, comparison_id: int):
        super().__init__()
        self.user_id = user_id
        self.comparison_id = comparison_id
        self.template_path = TEMPLATE_PATH

    def _get_user_name(self) -> str:
        with Session(engine) as session:
            user = session.exec(select(Users).where(Users.id == self.user_id)).one()
            return user.name

    def _get_cover_letter_paragraphs(self) -> list[dict[str, Any]]:
        with Session(engine) as session:
            paragraphs = session.exec(  # type: ignore
                select(CoverLetterParagraphs)
                .where(CoverLetterParagraphs.comparison_id == self.comparison_id)
                .order_by(CoverLetterParagraphs.paragraph_number)  # type: ignore
            ).all()
            return [para.dict() for para in paragraphs]

    def build_cover_letter(self) -> bytes:
        # 1. Load the template
        latex_template = self._load_template(self.template_path)

        # 2. Get and format all the data
        paragraphs = self._get_cover_letter_paragraphs()

        # 3. Replace placeholders in the template with formatted content
        replacements = {
            "CANDIDATENAME": self._get_user_name(),
            "PARAGRAPH1": self._escape_latex(paragraphs[0]["paragraph_text"])
            if len(paragraphs) > 0
            else "",
            "PARAGRAPH2": self._escape_latex(paragraphs[1]["paragraph_text"])
            if len(paragraphs) > 1
            else "",
            "PARAGRAPH3": self._escape_latex(paragraphs[2]["paragraph_text"])
            if len(paragraphs) > 2
            else "",
            "PARAGRAPH4": self._escape_latex(paragraphs[3]["paragraph_text"])
            if len(paragraphs) > 3
            else "",
            "PARAGRAPH5": self._escape_latex(paragraphs[4]["paragraph_text"])
            if len(paragraphs) > 4
            else "",
        }

        filled_latex = self._replace_placeholders(latex_template, replacements)

        # 4. Generate PDF
        output_path = os.path.join(
            ROOT_PATH, "media", f"cover_letter_{self.comparison_id}"
        )
        pdf_bytes = self.generate_pdf(
            latex_content=filled_latex, output_path=output_path
        )

        # 5. Save to database
        self._save_cover_letter_to_database(pdf_bytes)

        return pdf_bytes

    def _save_cover_letter_to_database(self, pdf_bytes: bytes):
        with Session(engine) as session:
            comparison = session.exec(
                select(Comparisons).where(Comparisons.id == self.comparison_id)
            ).first()
            if comparison:
                comparison.cover_letter = pdf_bytes
                session.add(comparison)
                session.commit()
            else:
                raise ValueError("Comparison not found in database.")
