import os
import random
from sqlmodel import Session, select
from langchain.prompts import PromptTemplate
from langchain_community.callbacks import get_openai_callback


from app.core.db import engine
from app.llm import ModelNames
from app.llm.base_builder import BaseBuilder
from app.logger import Logger
from app.models import (
    UserJobPostingComparisons,
    CoverLetterParagraphs,
    CoverLetterParagraphExamples,
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


COVER_LETTER_TEMPLATE = """
    {{
    "context": {{
        "role": "Career Advising Expert",
        "action": "Craft a tailored cover letter",
        "objective": "Produce a compelling cover letter that enhances the candidate's chance of securing an interview by emphasizing relevant qualifications and achievements.",
        "examples": "For each paragraph, examples including poor responses and their corrections will be provided. Use these as guidance to tailor the cover letter specifically to the job without misleading content."
    }},
    "inputs":{{
        "job_posting_data":"{job_posting_data}",
        "candidate_work_experiences":"{parsed_work_experiences}",
        "candidate_education":"{parsed_educations}",
        "candidate_skills":"{parsed_skills}",
        "candidate_languages":"{parsed_languages}",
        "candidate_personal_info": "{user_additional_info}"
    }}
    
    "instructions":{{
        "cover_letter_sttructure": {{
            "first_paragraph": {{
                "length": "2 sentences",
                "content": "Introduce the candidate's professional intent and connection to the company.",
                "guidelines": {{
                    "highlight_strengths": "Emphasize strengths and align with the company's values.",
                    "conciseness": "Be concise, use examples where possible."
                }},
                "examples": "{first_paragraph_examples}"
            }},
            "second_paragraph": {{
                "content": "Discuss a key qualification that matches the job requirements.",
                "link": "Link the qualification to any of the themes"
                "guidelines": {{
                    "themes": [
                        "Leadership", "Initiative", "Challenging Work",
                        "Versatility", "Resilience", "Conflict Management", "Curiosity"
                    ],   
                    "structure": "Theme --> Context --> Action --> Result",
                }}
                "examples": "{second_paragraph_examples}"
            }},
            "third_paragraph": {{
                "guidelines": "same as second_paragraph",
                "examples": "{third_paragraph_examples}"
            }},
            "fourth_paragraph": {{
                "content": "Highlight admiration for the company’s values and industry position.",                
                "guidelines": {{
                    "personal_touch": "Use personal anecdotes or the candidate personal info to match the company’s values or services.",
                    "honesty": "Ensure the reasons for interest in the company are genuine."
                }},
                "structure_examples": [
                    "I’ve been following [COMPANY] for a couple of months now and I align with both the company’s values and its general direction. The [VALUE] really stands out to me because [REASON]."
                ],
                "examples": "{fourth_paragraph_examples}"
            }},
            "fifth_paragraph": {{
                "content": "Summarize the candidate's enthusiasm and readiness for the position.",
                "guidelines": {{
                    "conciseness": "Be concise and clear, prioritize examples and numbers, use less words.",
                    "closing_statement": "Express anticipation for a response."
                }},
                "examples": "{fifth_paragraph_examples}"
            }},
        }},
    }},
    "restrictions": {{
        "format": "You must provide only 5 paragraphs according to the instructions. Do not add intros like dear hiring manager or thanks or sincerely. Just the 5 paragraphs.",
        "length": "The cover letter must be limited to 350 words.",
        "action_focus": "Highlight measurable achievements and actions.",
        "forbidden_words": [
            "extensive", "seasoned", "appeals", "advanced", "resonates",
            "spearhead", "honed", "efficient", "ethos", "keen"
        ],
        "style": "Remove all adverbs and adjectives from the final draft.",
        "name":  "Do not include the name of the candidate in any paragraph."
        "implicit_fit": "Demonstrate suitability through examples, not direct statements."
    }}
}}
    """


class CoverLetterBuilder(BaseBuilder):
    def __init__(
        self,
        model_name: str,
        user_id: int,
        temperature: float = 0,
        log_file_name="llm.log",
        log_prefix="CoverLetterBuilder",
        template_name="cover_letter.tex",
    ):
        super().__init__(
            model_name=model_name,
            user_id=user_id,
            temperature=temperature,
            log_file_name=log_file_name,
            log_prefix=log_prefix,
        )
        self.template_name = template_name
        self.examples = self._get_examples_from_db()
        self._create_chain()

    def _get_examples_from_db(self):
        with Session(engine) as session:
            examples_dict = {}
            for i in range(1, 6):
                comparisons = session.exec(
                    select(UserJobPostingComparisons).where(
                        UserJobPostingComparisons.user_id == self.user_id
                    )
                ).all()
                comparison_ids = [comparison.id for comparison in comparisons]
                examples = session.exec(
                    select(CoverLetterParagraphExamples).where(
                        CoverLetterParagraphExamples.comparison_id.in_(comparison_ids),  # type: ignore
                        CoverLetterParagraphExamples.paragraph_number == i,
                    )
                ).all()
                examples = random.sample(examples, min(3, len(examples)))

                examples_dict[f"paragraph_{i}"] = [
                    {
                        "original": example.original_paragraph_text,
                        "well_done": example.edited_paragraph_text,
                    }
                    for example in examples
                ]
        return examples_dict

    def _create_chain(self):
        self.template = PromptTemplate(
            template=COVER_LETTER_TEMPLATE,
            input_variables=[
                "job_posting_data",
                #  "requirement_qualification_comparison"
            ],
            partial_variables={
                "user_additional_info": self._get_user_attribute("additional_info"),
                "parsed_work_experiences": self._get_user_attribute(
                    "parsed_work_experiences"
                ),
                "parsed_educations": self._get_user_attribute("parsed_educations"),
                "parsed_skills": self._get_user_attribute("parsed_skills"),
                "parsed_languages": self._get_user_attribute("parsed_languages"),
                "first_paragraph_examples": self.examples["paragraph_1"],
                "second_paragraph_examples": self.examples["paragraph_2"],
                "third_paragraph_examples": self.examples["paragraph_3"],
                "fourth_paragraph_examples": self.examples["paragraph_4"],
                "fifth_paragraph_examples": self.examples["paragraph_5"],
            },
        )
        self.chain = self.template | self.llm | self.output_parser

    def _update_tex_template(
        self, template, paragraphs: list[str], candidate_name: str
    ):
        # Ensure there are exactly five paragraphs to replace the placeholders
        if len(paragraphs) != 5:
            raise ValueError("The list must contain exactly 5 paragraphs.")

        # Replace the placeholders with the corresponding paragraphs
        for i, paragraph in enumerate(paragraphs, start=1):
            placeholder = f"PARAGRAPH{i}"
            template = template.replace(placeholder, self._escape_latex(paragraph))

        # Replace the placeholder for the candidate's name
        template = template.replace("CANDIDATENAME", candidate_name)

        return template

    def _run_chain(self, job_id: int):
        with get_openai_callback() as cb:
            result = self.chain.invoke(
                {
                    "job_posting_data": self._get_job_summary(job_id=job_id),
                    "requirement_qualification_comparison": self._get_comparison_summary(
                        job_id=job_id
                    ),
                }
            )
            self.logger.info(
                f"Built Cover Letter for user {self.user_id} and {job_id}: \n {cb}"
            )
            return result

    def _save_paragraphs_to_database(
        self, job_id: int, cover_letter_paragraphs: list[str]
    ):
        if len(cover_letter_paragraphs) != 5:
            raise ValueError("The list must contain exactly 5 paragraphs.")
        with Session(engine) as session:
            # get the comparison id
            comparison = (
                session.query(UserJobPostingComparisons)
                .filter_by(job_posting_id=job_id, user_id=self.user_id)
                .first()
            )
            if comparison:
                session.query(CoverLetterParagraphs).filter_by(
                    comparison_id=comparison.id
                ).delete()
                for i, paragraph in enumerate(cover_letter_paragraphs, start=1):
                    session.add(
                        CoverLetterParagraphs(
                            comparison_id=comparison.id,
                            paragraph_text=paragraph,
                            paragraph_number=i,
                        )
                    )
                session.commit()
            else:
                self.logger.error("Comparison not found in database.")

    def _save_cover_letter_to_database(self, job_id: int, pdf_bytes: bytes):
        with Session(engine) as session:
            comparison = (
                session.query(UserJobPostingComparisons)
                .filter_by(job_posting_id=job_id, user_id=self.user_id)
                .first()
            )
            if comparison:
                comparison.cover_letter = pdf_bytes
                session.commit()
            else:
                self.logger.error("Comparison not found in database.")

    def _build(self, job_id: int, use_llm: bool = True):
        self.logger.info(f"Building letter for user {self.user_id}" and f"Job {job_id}")

        if use_llm:
            letter_content = self._run_chain(job_id=job_id)
            if ":" in letter_content:
                letter_content = letter_content.split(":")[1]
            letter_content = [line for line in letter_content.split("\n") if line != ""]
            self._save_paragraphs_to_database(
                job_id=job_id, cover_letter_paragraphs=letter_content
            )
        else:
            # Get the paragraphs from the database
            with Session(engine) as session:
                comparison = (
                    session.query(UserJobPostingComparisons)
                    .filter_by(job_posting_id=job_id, user_id=self.user_id)
                    .first()
                )
                if comparison:
                    paragraphs = (
                        session.query(CoverLetterParagraphs)
                        .filter_by(comparison_id=comparison.id)
                        .order_by(CoverLetterParagraphs.paragraph_number)
                        .all()
                    )
                    if paragraphs:
                        letter_content = [
                            paragraph.paragraph_text for paragraph in paragraphs
                        ]
                    else:
                        self.logger.error("There are no paragraphs")
                        raise ValueError("There are no paragraphs")
                else:
                    self.logger.error("Comparison not found in database.")
                    raise ValueError("Comparison not found in database.")

        with open(os.path.join(ROOT_DIR, "templates", self.template_name), "r") as file:
            cover_letter_tex = self._update_tex_template(
                template=file.read(),
                paragraphs=letter_content,
                candidate_name=self._get_user_attribute("name"),
            )
            pdf_bytes = self._create_pdf_from_latex(
                latex_string=cover_letter_tex,
                path=os.path.join(
                    ROOT_DIR,
                    "media",
                    f"{self.user_id}",
                    f"{self._get_job_company_and_position(job_id)}_cover_letter",
                ),
            )
            if pdf_bytes:
                self._save_cover_letter_to_database(job_id=job_id, pdf_bytes=pdf_bytes)
            else:
                self.logger.error("Failed to create PDF from LaTeX for cover letter")
        self._cleanup_build_directory(
            os.path.join(ROOT_DIR, "media", f"{self.user_id}")
        )


if __name__ == "__main__":
    cover_letter_builder = CoverLetterBuilder(
        model_name=ModelNames.GPT4_TURBO, user_id=1, temperature=0.4
    )
    cover_letter_builder.build(job_ids=[3872266079, 3872263836])
