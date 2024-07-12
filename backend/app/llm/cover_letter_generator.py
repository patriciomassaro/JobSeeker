from pydantic import BaseModel, Field
import random
from sqlmodel import Session, select


from app.core.db import engine
from app.llm.base_generator import BaseGenerator
from app.models import (
    Comparisons,
    CoverLetterParagraphs,
    CoverLetterParagraphExamples,
    LLMTransactionTypesEnum,
)


class CoverLetterParagraphLLM(BaseModel):
    paragraph_number: int = Field(
        description="The order of the paragraph in the cover letter."
    )
    content: str = Field(description="The text content of the paragraph.")


class CoverLetterParagraphsLLM(BaseModel):
    paragraphs: list[CoverLetterParagraphLLM] = Field(
        description="List of cover letter paragraphs."
    )


SYSTEM_PROMPT_TEMPLATE = r"""
    {{
        "context": {{
            "role": "Career Advising Expert",
            "action": "Craft a tailored cover letter",
            "objective": "Produce a compelling cover letter that enhances the candidate's chance of securing an interview by emphasizing relevant qualifications and achievements.",
            "examples": "For each paragraph, examples including poor responses and their corrections will be provided. Use these as guidance to tailor the cover letter specifically to the job without misleading content."
        }},
        "instructions":{{
            "cover_letter_sttructure": {{
                "first_paragraph": {{
                    "length": "2 sentences",
                    "content": "Introduce the candidate's professional intent and connection to the company.",
                    "guidelines": {{
                        "highlight_strengths": "Emphasize strengths and align with the company's values.",
                        "conciseness": "Be concise, use examples where possible."
                    }},
                    "examples": {examples_paragraph_1}
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
                    "examples": {examples_paragraph_2}
                }},
                "third_paragraph": {{
                    "guidelines": "same as second_paragraph",
                    "examples": {examples_paragraph_3}
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
                        "examples": {examples_paragraph_4}
                    }},
                    "fifth_paragraph": {{
                        "content": "Summarize the candidate's enthusiasm and readiness for the position.",
                        "guidelines": {{
                            "conciseness": "Be concise and clear, prioritize examples and numbers, use less words.",
                            "closing_statement": "Express anticipation for a response."
                        }},
                        "examples":  {examples_paragraph_5}
                    }},
                }},
        }},
        "restrictions": {{
            "output_format": {format_requirements},
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


USER_PROMPT_TEMPLATE = r"""
  "inputs":{{
        "job_posting_data":{job_summary},
        "candidate_work_experiences":{work_experiences},
        "candidate_education":{educations},
        "candidate_skills":{skills},
        "candidate_languages":{languages},
        "candidate_personal_info":{additional_info}
    }}
"""


class CoverLetterGenerator(BaseGenerator):
    def __init__(
        self,
        model_name: str,
        user_id: int,
        job_posting_id: int,
        comparison_id: int,
        temperature: float = 0,
        log_file_name="llm.log",
        log_prefix="CoverLetterBuilder",
    ):
        super().__init__(
            model_name=model_name,
            user_id=user_id,
            job_posting_id=job_posting_id,
            temperature=temperature,
            log_file_name=log_file_name,
            log_prefix=log_prefix,
            comparison_id=comparison_id,
        )
        self.output_pydantic_model = CoverLetterParagraphsLLM

    def _get_examples_from_db(self):
        with Session(engine) as session:
            examples_dict = {}
            for i in range(1, 6):
                comparisons = session.exec(
                    select(Comparisons).where(Comparisons.user_id == self.user_id)
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

    def _create_system_prompt(self):
        examples = self._get_examples_from_db()
        return SYSTEM_PROMPT_TEMPLATE.format(
            examples_paragraph_1=examples["paragraph_1"],
            examples_paragraph_2=examples["paragraph_2"],
            examples_paragraph_3=examples["paragraph_3"],
            examples_paragraph_4=examples["paragraph_4"],
            examples_paragraph_5=examples["paragraph_5"],
            format_requirements=self.output_pydantic_model.model_json_schema(),
        )

    def _create_user_prompt(self) -> str:
        comparison_data = self._get_comparison_data()
        return USER_PROMPT_TEMPLATE.format(
            job_summary=comparison_data["job_info"]["summary"],
            work_experiences=comparison_data["user_attributes"]["work_experiences"],
            educations=comparison_data["user_attributes"]["parsed_educations"],
            skills=comparison_data["user_attributes"]["parsed_skills"],
            languages=comparison_data["user_attributes"]["parsed_languages"],
            additional_info=comparison_data["user_attributes"]["additional_info"],
        )

    def _save_paragraphs_to_database(self, paragraphs: list[CoverLetterParagraphLLM]):
        with Session(engine) as session:
            comparison = session.exec(
                select(Comparisons).where(
                    Comparisons.job_posting_id == self.job_posting_id,
                    Comparisons.user_id == self.user_id,
                )
            ).one_or_none()

            if not comparison:
                raise ValueError("Comparison not found in database.")

            # Delete existing paragraphs for this comparison
            old_paragraphs = session.exec(
                select(CoverLetterParagraphs).where(
                    CoverLetterParagraphs.comparison_id == comparison.id
                )
            ).all()
            session.delete(old_paragraphs) if old_paragraphs else None

            # Insert new paragraphs
            new_paragraphs = [
                CoverLetterParagraphs(
                    comparison_id=comparison.id,
                    paragraph_number=para.paragraph_number,
                    paragraph_text=para.content,
                )
                for para in paragraphs
            ]
            session.add_all(new_paragraphs)

            session.commit()

    def generate_cover_letter_paragraphs(self):
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt()

        print("SYSTEM PROMPT: \n\n", system_prompt)
        print("USER PROMPT: \n\n", user_prompt)

        cover_letter_paragraphs, transaction_summary = self._generate_and_parse_content(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_type=LLMTransactionTypesEnum.COVER_LETTER_GENERATION,
            pydantic_model=self.output_pydantic_model,
        )

        if isinstance(cover_letter_paragraphs, CoverLetterParagraphsLLM):
            self._save_paragraphs_to_database(cover_letter_paragraphs.paragraphs)
        else:
            raise ValueError(
                f"Unexpected type for parsed_content: {type(cover_letter_paragraphs)}"
            )
