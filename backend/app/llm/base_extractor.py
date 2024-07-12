import json
from pydantic import BaseModel
from app.logger import Logger
from app.llm import LLMInitializer, LLMTransactionSummary
from app.models import LLMTransactionTypesEnum


class BaseLLMExtractor:
    def __init__(
        self,
        model_name: str,
        pydantic_object: BaseModel,
        user_id: int,
        temperature: float = 0,
        log_file_name="llm.log",
        log_prefix="LLMExtractor",
    ):
        self.user_id = user_id
        self.llm = LLMInitializer(
            model_name=model_name, temperature=temperature, user_id=user_id
        )
        self.pydantic_object = pydantic_object
        self.logger = Logger(
            prefix=log_prefix, log_file_name=log_file_name
        ).get_logger()
        self.system_prompt = f"""
            You are an expert extraction algorithm. If you do not know the value of an attribute asked to extract, return null for the attribute's value.

            Please extract the following information from the given text and format it as a JSON object:
             {self.pydantic_object.model_json_schema()}


            Only respond the extracted data in JSON format, without any markdown notation.
            """

    def extract_data_from_text(
        self,
        text: str,
        task_type: LLMTransactionTypesEnum,
        job_posting_id: int | None = None,
    ) -> tuple[dict, LLMTransactionSummary]:
        transaction = self.llm.get_completion(
            system_prompt=self.system_prompt,
            user_prompt=f"Text to extract from: {text}",
            task_type=task_type,
            job_posting_id=job_posting_id,
        )
        try:
            extracted_data = json.loads(transaction.text)
            validated_data = self.pydantic_object(**extracted_data)  # type: ignore
            self.logger.info("Extracted and validated data from text")
            return validated_data.dict(), transaction
        except json.JSONDecodeError:
            self.logger.error("Failed to parse JSON from LLM response")
            raise
        except ValueError as e:
            self.logger.error(f"Validation error: {str(e)}")
            raise
