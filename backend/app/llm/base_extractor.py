from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel
from langchain_community.callbacks import get_openai_callback
from app.logger import Logger
import warnings
from pydantic.json_schema import PydanticJsonSchemaWarning

warnings.filterwarnings("ignore", category=PydanticJsonSchemaWarning)


from app.llm import LLMInitializer


CV_DATA_EXTRACTOR_SYSTEM_PROMPT_TEXT = "You are an expert extraction algorithm. If you do not know the value of an attribute asked to extract, return null for the attribute's value. \n {format_instructions} \n {input}"


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
        self.llm = self.llm_init.get_llm()
        self.output_parser = JsonOutputParser(pydantic_object=pydantic_object)
        self.template = PromptTemplate(
            template=CV_DATA_EXTRACTOR_SYSTEM_PROMPT_TEXT,
            input_variables=["input"],
            partial_variables={
                "format_instructions": self.output_parser.get_format_instructions()
            },
        )
        self.logger = Logger(
            prefix=log_prefix, log_file_name=log_file_name
        ).get_logger()
        self.chain = self.template | self.llm | self.output_parser

    def extract_data_from_text(self, text: str) -> dict:
        with get_openai_callback() as cb:
            result = self.chain.invoke({"input": text})
            self.logger.info(f"Extracted data from text: \n {cb}")
            return result
