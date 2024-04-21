import time
import subprocess
import os
import json
import re
import glob
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.callbacks import get_openai_callback


from jobseeker.llm import LLMInitializer, ModelNames
from jobseeker.llm.base_builder import BaseBuilder
from jobseeker.logger import Logger

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CV_PROMPT_TEMPLATE = """
        You are a seasoned career advising expert in crafting resumes and cover letters.
        I will provide you with a job description, a resume data in tex format and a comparison of the job description requirements and the resume qualifications that another expert did.
        Your objective is to tailor the resume to the job description, highligting the most relevant qualifications and using the technologies and skill names that the job description uses.


        Follow these instructions to tailor the resume to the job description:

        - Your output is a tex file and only a tex file, remember to check for .
        - KEEP IT SIMPLE
        - You may change the job titles (Example: change ML engineer to Data Scientist), but don't lie about the roles.
        - DONT LIE ABOUT THE ROLES, IF THE PERSON NEVER WORKED IN PAYMENTS, dont add payments on their resume. Focus on technologies and skills.
        - Sentences should be action-oriented: I did X in the context of Y and achieved Z
          Example: Created first integration playbook resulting in successful API integrations with major client, leading to 5M increase in yearly revenue
        - Do not delete any of the items, just change the words
        - Do not add jargon, buzzwords




        This is the .tex file that represents the CV

        ------
        {cv_tex}
        ------

        This is all the information that the client gathered about the job posting:
        ------
        {job_posting_data}
        ------

        A colleague of yours has compared the job posting requirements with the resume qualifications, here is the comparison:

        ------
        {requirement_qualification_comparison}
        ------


    When you finish writing the CV, read it line by line and think if it makes sense.
        
    """



class CVBuilder(BaseBuilder):
    def __init__(self,
                 model_name:ModelNames,
                 user_id:int,
                 user_cv_data:dict,
                 user_cv_latex:str,
                 temperature:float = 0,
                 log_file_name="llm.log",
                 log_prefix="CoverLetterBuilder",
                 latex_template_name: str = "cover_letter.tex",
                 ):
        super().__init__(model_name=model_name,
                         user_id=user_id,
                         user_cv_data=user_cv_data,
                         user_cv_latex=user_cv_latex,
                         prompt_template=CV_PROMPT_TEMPLATE,
                         latex_template_name=latex_template_name,
                         temperature=temperature,
                         log_file_name=log_file_name,
                         log_prefix=log_prefix)

    def get_cv_from_llm(self,job_data:str,requirement_qualification_comparison:str):
        with get_openai_callback() as cb:
            result = self.chain.invoke({"job_posting_data":job_data,
                                        "requirement_qualification_comparison":requirement_qualification_comparison})
            self.logger.info(f"Built CV for user {self.user_id} \n {cb}")
            return result

    @staticmethod
    def clean_latex_string(latex_string:str):
        return latex_string.replace("```tex","").replace("```","")


    def build(self,requirement_qualification_comparison:str,job_data :str,job_id:int):
        self.logger.info(f"Building CV for user {self.user_id}" and f"Job {job_id}")
        custom_cv_latex = self.get_cv_from_llm(job_data,requirement_qualification_comparison)
        custom_cv_latex = self.clean_latex_string(custom_cv_latex)
        
        self.create_pdf_from_latex(latex_string=custom_cv_latex,
                                       path=os.path.join(ROOT_DIR, "media", f"{self.user_id}", f"{job_id}_CV"))
        self.cleanup_build_directory(os.path.join(ROOT_DIR, "media", f"{self.user_id}"))
            
            




        
