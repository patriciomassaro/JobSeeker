import os
import json
from pydantic import BaseModel, ValidationError
from sqlmodel import Session, select, and_
from typing import TypeVar, Generic

from app.models import Users, JobPostings, Comparisons
from app.core.db import engine
from app.llm import LLMInitializer, LLMTransactionSummary, LLMTransactionTypesEnum
from app.logger import Logger


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = TypeVar("T", bound=BaseModel)


class CustomJSONParser(Generic[T]):
    def __init__(self, pydantic_model: type[T]):
        self.pydantic_model = pydantic_model

    def parse(self, json_string: str) -> T:
        try:
            data = json.loads(json_string)
            return self.pydantic_model.model_validate(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")
        except ValidationError as e:
            raise ValueError(f"Validation error: {str(e)}")


class BaseGenerator:
    def __init__(
        self,
        model_name: str,
        user_id: int,
        job_posting_id: int,
        comparison_id: int,
        temperature: float = 0,
        log_file_name="llm.log",
        log_prefix="Builder",
    ):
        self.llm = LLMInitializer(
            model_name=model_name, temperature=temperature, user_id=user_id
        )
        self.user_id = user_id
        self.job_posting_id = job_posting_id
        self.comparison_id = comparison_id
        self.logger = Logger(
            prefix=log_prefix, log_file_name=log_file_name
        ).get_logger()

    def _get_comparison_data(self) -> dict:
        with Session(engine) as session:
            query = (
                select(  # type: ignore
                    Users.parsed_work_experiences,
                    Users.parsed_skills,
                    Users.parsed_educations,
                    Users.parsed_languages,
                    Users.additional_info,
                    JobPostings.summary,
                    JobPostings.title,
                    JobPostings.company,
                    Comparisons.comparison,
                )
                .select_from(Users)
                .join(Comparisons, Users.id == Comparisons.user_id)
                .join(JobPostings, Comparisons.job_posting_id == JobPostings.id)
                .where(
                    Comparisons.id == self.comparison_id,
                )
            )
            result = session.exec(query).first()

            if result:
                return {
                    "user_attributes": {
                        "work_experiences": result.parsed_work_experiences,
                        "parsed_skills": result.parsed_skills,
                        "parsed_educations": result.parsed_educations,
                        "parsed_languages": result.parsed_languages,
                        "additional_info": result.additional_info,
                    },
                    "job_info": {
                        "summary": json.dumps({"summary": result.summary}),
                    },
                    "comparison_summary": json.dumps({"comparison": result.comparison}),
                }
            else:
                e = f"Could not find the user {self.user_id} or job posting {self.job_posting_id}"
                self.logger.error(e)
                raise ValueError(e)

    def _generate_and_parse_content(
        self,
        system_prompt: str,
        user_prompt: str,
        task_type: LLMTransactionTypesEnum,
        pydantic_model: type[BaseModel],
    ) -> tuple[BaseModel, LLMTransactionSummary]:
        response = self.llm.get_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_type=task_type,
            job_posting_id=self.job_posting_id,
            comparison_id=self.comparison_id,
        )
        response.text = response.text.replace("```json", "").replace("```", "")

        try:
            parsed_content = CustomJSONParser(pydantic_model).parse(response.text)
        except ValueError as e:
            self.logger.error(f"Error parsing content: {str(e)}")
            raise

        return parsed_content, response

    # def _cleanup_build_directory(self, path):
    #     time.sleep(1)
    #     pattern = r"media/\d+"
    #     # Check if the path matches the expected pattern
    #     if not re.search(pattern, path):
    #         self.logger.error(f"The path does not match the expected pattern: {path}")
    #         raise ValueError("The path does not match the expected pattern.")
    #
    #     for file in glob.glob(path + "/*"):
    #         if file.endswith(".pdf") or file.endswith(".tex"):
    #             continue
    #         # delete the file
    #         os.remove(file)
    #
    # def _create_pdf_from_latex(self, latex_string, path) -> bytes | None:
    #     directory = os.path.dirname(path)
    #     tex_file_path = f"{path}.tex"
    #     pdf_file_path = f"{path}.pdf"
    #
    #     if not os.path.exists(directory):
    #         os.makedirs(directory)
    #
    #     with open(tex_file_path, "w") as file:
    #         file.write(latex_string)
    #
    #     current_dir = os.getcwd()
    #     os.chdir(directory)
    #     process = subprocess.run(
    #         ["pdflatex", "-interaction=nonstopmode", tex_file_path],
    #         text=True,
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.PIPE,
    #     )
    #     os.chdir(current_dir)
    #
    #     if process.returncode != 0:
    #         self.logger.error(
    #             f"Failed to compile the LaTeX file: \n {process.stdout} \n {process.stderr}"
    #         )
    #         return None
    #
    #     try:
    #         with open(pdf_file_path, "rb") as pdf_file:
    #             pdf_bytes = pdf_file.read()
    #         return pdf_bytes
    #     except Exception as e:
    #         self.logger.error(f"Failed to read the PDF file: {str(e)}")
    #         return None
    # @staticmethod
    # def _escape_latex(string: str):
    #     # Mapping of LaTeX special characters that need to be escaped
    #     latex_special_chars = {
    #         "&": r"\&",
    #         "%": r"\%",
    #         "$": r"\$",
    #         "#": r"\#",
    #         "_": r"\_",
    #         "{": r"\{",
    #         "}": r"\}",
    #         "~": r"\textasciitilde{}",
    #         "^": r"\^{}",
    #         "\\": r"\textbackslash{}",
    #     }
    #
    #     # Use a list to build the escaped string
    #     escaped_parts = []
    #     i = 0
    #     while i < len(string):
    #         if string[i] in latex_special_chars and (i == 0 or string[i - 1] != "\\"):
    #             # Append the escaped character if it's not already escaped
    #             escaped_parts.append(latex_special_chars[string[i]])
    #         else:
    #             # Append the character as is
    #             escaped_parts.append(string[i])
    #         i += 1
    #     return "".join(escaped_parts)
    #
    # @staticmethod
    # def _clean_latex_code_header(latex_code: str) -> str:
    #     return (
    #         latex_code.replace("```latex", "").replace("```tex", "").replace("```", "")
    #     )
