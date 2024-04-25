import json
import os
from langchain.prompts import PromptTemplate
from langchain_community.callbacks import get_openai_callback


from jobseeker.llm import LLMInitializer, ModelNames
from jobseeker.llm.base_builder import BaseBuilder
from jobseeker.logger import Logger

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CV_PROMPT_TEMPLATE ='''
{{
    "context": {{
        "role": "career advising expert",
        "action": "tailor the resume to the job description",
        "objective": "Assist the client in customizing their resume to align with a specific job description by emphasizing pertinent qualifications and incorporating appropriate technologies and skills from the job description.",
        "inputs": {{
            "job_posting_data": "{job_posting_data}",
            "applicant_cv": "{applicant_cv}",
            "requirement_qualification_comparison": "{requirement_qualification_comparison}",
            "resume_template": "{cv_template}"
        }},
    }},
    "instructions": {{
        "output": "Produce a tailored resume in TeX format, keeping the structure of the input resume",
        "format_requirements": "Ensure all special characters are properly escaped in the TeX file, e.g., use '\\' for special characters like '%'.",
        "comparisons": "You can use the requirement_qualification_comparison input to build the resume, but you are not obliged to use it. Leverage on the job_posting_data input to build the resume too.",
        "content_guidelines": {{
            "job_titles": "You may change the job titles, but don't lie. An example: change 'ML engineer' to 'Data Scientist'.",
            "industries": "Retain truthfulness about industries; emphasize relevant skills and technologies.",
            "business_applications": "Do not lie about the business applications, if the candidate never worked in payments, don't say they did.",
            "sentence_style": "Construct sentences that are action-oriented: 'I performed X, resulting in Y in the context of Z.'",
            "language": "Avoid adjectives and adverbs; focus on verifiable achievements.",
            "modification_rules": "Do not remove any items; instead, rephrase them for relevance and impact.",
            "redundancy": "Avoid redundancy; ensure each part of the resume contributes uniquely to the overall narrative.",
        }}
    }},
    "restrictions": {{
        "number of items": "Mention all of the provided accomplishments by the candidate in the resume. If they are not relevant, keep them as they are.",
        "experiences": "ALL EXPERIENCES from the profile MUST BE INCLUDED IN THE RESUME. Do not delete any work experience",
        "verb_tense": "keep the verb tense consistent throughout the resume.",
        "template": "Use the provided resume template as a base for the new resume."
    }}
}}
'''

# CV_PROMPT_TEMPLATE ='''
# {{
#     "context": {{
#         "role": "career advising expert",
#         "action": "tailor the resume to the job description",
#         "objective": "Assist the client in customizing their resume to align with a specific job description by emphasizing pertinent qualifications and incorporating appropriate technologies and skills from the job description.",
#         "inputs": {{
#             "job_posting_data": "{job_posting_data}",
#             "requirement_qualification_comparison": "{requirement_qualification_comparison}",
#             "resume": "{cv_tex}"
#         }},
#     }},
#     "instructions": {{
#         "output": "Produce a tailored resume in TeX format, keeping the structure of the input resume",
#         "format_requirements": "Ensure all special characters are properly escaped in the TeX file, e.g., use '\\' for special characters like '%'.",
#         "content_guidelines": {{
#             "job_titles": "You may change the job titles, but don't lie. An example: change 'ML engineer' to 'Data Scientist'.",
#             "industries": "Retain truthfulness about industries; emphasize relevant skills and technologies.",
#             "business_applications": "Do not lie about the business applications, if the candidate never worked in payments, don't say they did.",
#             "sentence_style": "Construct sentences that are action-oriented: 'I performed X, resulting in Y in the context of Z.'",
#             "language": "Avoid adjectives and adverbs; focus on verifiable achievements.",
#             "modification_rules": "Do not remove any items; instead, rephrase them for relevance and impact.",
#             "redundancy": "Avoid redundancy; ensure each part of the resume contributes uniquely to the overall narrative.",
#         }}
#     }},
#     "restrictions": {{
#         "quality_assurance": "The resume must reflect high-quality customization that aligns with the job description, demonstrating the candidate’s suitability for the role with no content repetition.",
#         "achievements": "Each resume entry should be linked to tangible outcomes or newly framed achievements tailored to the job posting.",
#         "work_experience": "Do not delete any work experience; instead, rephrase it to align with the job description.",
#         "number of items": "the resume should have the exact number of items as the input resume.",
#         "verb_tense": "keep the verb tense consistent throughout the resume.",
#     }}
# }}
# '''

# CV_PROMPT_TEMPLATE = """

#         You are a seasoned career advising expert in crafting resumes and cover letters.
#         I will provide you with a job description, a resume data in tex format and a comparison of the job description requirements and the resume qualifications that another expert did.
#         Your objective is to tailor the resume to the job description, highligting the most relevant qualifications and using the technologies and skill names that the job description uses.


#         Follow these instructions to tailor the resume to the job description:

#         - Your output is a tex file and only a tex file, remember to check for escape characters.
#         - Don't forget to add \\ when using special characters like %.
#         - It must be short
#         - You may change the job titles (Example: change ML engineer to Data Scientist), but don't lie about the roles.
#         - do not lie about the industries where the candidate has worked, focus on the skills and technologies.
#         - Sentences should be action-oriented: I did X in the context of Y and achieved Z
#           Example: Created first integration playbook resulting in successful API integrations with major client, leading to 5M increase in yearly revenue
#         - Do not delete any of the items, just change the words
#         - Do not add jargon, buzzwords




#         This is the .tex file that represents the CV

#         ------
#         {cv_tex}
#         ------

#         This is all the information that the client gathered about the job posting:
#         ------
#         {job_posting_data}
#         ------

#         A colleague of yours has compared the job posting requirements with the resume qualifications, here is the comparison:

#         ------
#         {requirement_qualification_comparison}
#         ------        
#     """



class CVBuilder(BaseBuilder):
    def __init__(self,
                 model_name:ModelNames,
                 user_id:int,
                 temperature:float = 0,
                 log_file_name="llm.log",
                 log_prefix="CVBuilder",
                 ):
        super().__init__(model_name=model_name,
                         user_id=user_id,
                         temperature=temperature,
                         log_file_name=log_file_name,
                         log_prefix=log_prefix)
        self._create_chain()
        
    def _load_latex_to_string(self)->str:
        with open(os.path.join(ROOT_DIR, "media", f"{self.user_id}", "CV.tex"), "r") as file:
            return file.read()
    
    def _load_template_to_string(self)->str:
        with open(os.path.join(ROOT_DIR, "templates", "CV.tex"), "r") as file:
            return file.read()
        
    def _create_chain(self):
        self.template = PromptTemplate(
            template=CV_PROMPT_TEMPLATE,
            input_variables=["job_posting_data", "requirement_qualification_comparison"],
            partial_variables={
                "applicant_cv": self._get_user_summary(),
                "cv_template": self._load_template_to_string()
            }
        )
        self.chain = self.template | self.llm | self.output_parser

    def _run_chain(self,job_id:int):
        with get_openai_callback() as cb:
            result = self.chain.invoke({"job_posting_data":self._get_job_summary(job_id=job_id),
                                        "requirement_qualification_comparison":self._get_comparison_summary(job_id=job_id)})
            self.logger.info(f"Built CV for user {self.user_id} and {job_id} \n {cb}")
            return result

    def _build(self,job_id:int):
        self.logger.info(f"Building CV for user {self.user_id}" and f"Job {job_id}")
        custom_cv_latex = self._run_chain(job_id=job_id)
        custom_cv_latex = self._clean_latex_code_header(custom_cv_latex)
        self._create_pdf_from_latex(latex_string=custom_cv_latex,
                                       path=os.path.join(ROOT_DIR, "media", f"{self.user_id}", f"{self._get_job_company_and_position(job_id)}_CV"))
        self._cleanup_build_directory(os.path.join(ROOT_DIR, "media", f"{self.user_id}"))
            
if __name__ == "__main__":
    cv_builder = CVBuilder(model_name=ModelNames.GPT4_TURBO, user_id=1,temperature=0.3)
    cv_builder.build(job_ids=[ 3872263836])