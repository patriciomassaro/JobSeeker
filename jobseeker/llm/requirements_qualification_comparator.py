from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_community.callbacks import get_openai_callback
from pydantic import BaseModel
from typing import List

from jobseeker.logger import Logger
from jobseeker.llm import LLMInitializer,ModelNames

class RequirementsQualificationComparison(BaseModel):
    job_description_requirement:str = Field(...,description="The job description requirement")
    cv_qualification:str = Field(...,description="The cv qualification")
    cv_qualification_written_in_requirement_language:str = Field(...,description="The cv qualification, re-written to use the job description requirement language style")


class RequirementsQualificationComparisonList(BaseModel):
    requirements_qualification_comparisons:List[RequirementsQualificationComparison] = Field(...,description="A list of requirements and qualifications comparisons")

examples = [
    {
        "job_description_requirement": "2+ years of experience integrating with web APIs. Experience with modern web frameworks (React, Node.js, etc) is a plus",
        "cv_qualification": "For my programming school, I Built web applications using javascript, communicating with other services via requests.",
        "cv_qualification_written_in_requirement_language": "Build web applications using Node.js and Ruby, integrating APis from chess.com and Twitter. Did this for 2 years through online programming school.",
        "Reasoning behind": "Instead of Javascript, Node.js was written. Communicating with other services was changed to 'integrating using APIS' . Added the amount of years",
    },
    {
        "job_description_requirement": "Excellent communication skills; confortable leading meetings with executives.",
        "cv_qualification": "Reporting results to directors." ,
        "cv_qualification_written_in_requirement_language": "Reporting results to directors and leading meetings with executives.",
        "Reasoning behind": "Instead of just reporting, the word executive directors is added because it is mentioend in the job description. Leading meetings was added to match the job description requirement",

    }
]

REQUIREMENT_QUALIFICATION_COMPARISON_TEMPLATE = """
        You are a seasoned career advising expert in crafting resumes and cover letters.
        You specialize in creating compelling and tailored resumes and cover letters that highlight clients skills, experiences, and achievements—meticulously aligning with the specific job descriptions they target. 
        Your expertise extends across various industries, encompassing a deep understanding of prevailing hiring trends and Applicant Tracking Systems (ATS). 

        Your objective is to map job requirements with the client's qualification. Take this instructions into account:

        1. First requirements in the description are more important than the last ones and should be adressed.
        2. If you can't find a meaningful connection, DO NOT include it in the final output.
        3. Quantitative things like years of experience are nogotiable.
        4. Things like 'familiarity with' or 'advanced degree' or 'is a plus'  are negotiable.
        5. After you found a match. You have to rewrite the CV qualification to match the job description requirement language style

        Between lines, you may see examples 

        -------
        {examples}
        -------

        Pay close attention to the output instructions 

        -------
        {output_format_instructions}
        -------

        This is the cv that the client sent to you: 

        -----
        {cv_data}
        -----

        This is all the information that the client gathered about the job posting:

        ------
        {job_posting_data}
        ------
    """

class RequirementsQualificationsComparator:
    def __init__(self,
                 model_name:ModelNames,
                 cv_data:str,
                 temperature:float = 0,
                 log_file_name="llm.log",
                 log_prefix="RequirementsQualificationsComparator",
                 examples:List[dict]=examples
                 ):
        self.llm_init = LLMInitializer(model_name=model_name,temperature=temperature)
        self.llm = self.llm_init.get_llm()
        self.examples_str = self._generate_examples_string(examples=examples)
        self.output_parser = JsonOutputParser(pydantic_object=RequirementsQualificationComparisonList)
        self.template= PromptTemplate(
            template= REQUIREMENT_QUALIFICATION_COMPARISON_TEMPLATE,
            input_variables=["job_posting_data"],
            partial_variables={
                "output_format_instructions": self.output_parser.get_format_instructions(),
                "examples": self.examples_str,
                "cv_data": cv_data},
        )
        self.logger = Logger(prefix=log_prefix,log_file_name=log_file_name).get_logger()
        self.chain = self.template | self.llm | self.output_parser


    @staticmethod    
    def _generate_examples_string(examples:List[dict]):
        """
        Converts the example list to a string
        """
        return '\n'.join(f"EXAMPLE {index + 1}\n" + '\n'.join(f"{key}: {value}" for key, value in example.items())  
          for index, example in enumerate(examples)
        )

    def compare(self,text:str) -> dict:
        with get_openai_callback() as cb:
            result = self.chain.invoke({"job_posting_data":text})
            self.logger.info(f"Extracted data from text: \n {cb}")
            return result
