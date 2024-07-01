import json
from pydantic import BaseModel
from app.logger import Logger
from app.llm import LLMInitializer


class BaseLLMExtractor:
    def __init__(
        self,
        model_name: str,
        pydantic_object: BaseModel,
        temperature: float = 0,
        log_file_name="llm.log",
        log_prefix="LLMExtractor",
    ):
        self.llm_init = LLMInitializer(model_name=model_name, temperature=temperature)
        self.pydantic_object = pydantic_object
        self.logger = Logger(
            prefix=log_prefix, log_file_name=log_file_name
        ).get_logger()

    def get_prompt(self, text: str) -> str:
        return f"""
        You are an expert extraction algorithm. If you do not know the value of an attribute asked to extract, return null for the attribute's value.
        
        Please extract the following information from the given text and format it as a JSON object:
        
        {self.pydantic_object.schema_json()}
        
        Text to extract from:
        {text}
        """

    def extract_data_from_text(self, text: str) -> dict:
        prompt = self.get_prompt(text)
        messages = [{"role": "user", "content": prompt}]

        response = self.llm_init.get_completion(messages)

        try:
            extracted_data = json.loads(response)
            # Validate the extracted data against the Pydantic model
            validated_data = self.pydantic_object(**extracted_data)
            self.logger.info(f"Extracted and validated data from text")
            return validated_data.dict()
        except json.JSONDecodeError:
            self.logger.error("Failed to parse JSON from LLM response")
            raise
        except ValueError as e:
            self.logger.error(f"Validation error: {str(e)}")
            raise
