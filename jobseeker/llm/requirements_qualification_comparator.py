import json

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_community.callbacks import get_openai_callback
from pydantic import BaseModel
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed


from jobseeker.logger import Logger
from jobseeker.llm import LLMInitializer,ModelNames
from jobseeker.database import DatabaseManager
from jobseeker.database.models import (
    UserJobComparison as UserJobComparisonModel,
    JobPosting as JobPostingModel,
    Users as UsersModel
    )

class RequirementsQualificationComparison(BaseModel):
    priority:int = Field(...,description="In your opinion, how important is this requirement compared to the others?")
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

REQUIREMENT_QUALIFICATION_COMPARISON_TEMPLATE = '''{{
        "context":{{
            "role": "career advising consultant, expert in hiring trends and Applicant Tracking Systems (ATS)",
            "actions": 
                {{
                "step_1": "map job requirements with the client's qualifications",
                "step_2": "Rewrite the client's qualifications to match the job description requirement language style"
                }},
            "objective": "Your objective is to create requirement-qualification mappings so that a technical resume writer can use them to tailor the resume to the job description.",
            "inputs":
                {{
                    "job_posting_data": "{job_posting_data}",
                    "candidate_work_experience": "{parsed_worked_experiences}", 
                    "candidate_skills": "{parsed_skills}",
                }},
        }},
        "instructions":{{
            "step_1":{{
                    "priority": "First requirements in the description are more important than the last ones. Mandatory requirements are more important than optional ones.",
                    "negotiation": "Quantitative things like years of experience are negotiable if the gap is small. Things like 'familiarity with' or 'advanced degree' or 'is a plus' are negotiable.",
                    "if_no_match": "If you can't find a meaningful connection, DO NOT LIE in order to include it.",
                }},
            "step_2":{{
                "style": "The re-written qualification must be concise and action-oriented.",
                "structure": "The client did X in the context of Y and achieved Z.",
                "avoid_assumptions": "focus on describing the direct activities and outcomes from the CV, without extrapolating or assuming underlying skills unless explicitly stated. Avoid adding interpretations such as 'demonstrated proficiency' when converting qualifications into language matching job descriptions, unless such language is directly supported by the CV details"
                }},
            "examples": "{examples}"

        }},
        "restrictions":{{
            minimum_mathes_to_output: "6",
            "quality_assurance": "The re-written qualifications must reflect high-quality customization that aligns with the job description",
            "repetition": "Do not repeat the same qualification for multiple requirements",
            "adjectives": "Do not use adjectives or adverbs anywhere",
            "focus": "Focus on verifiable achievements",
            "output_format": "{output_format_instructions}"
        }}
}}


'''

# REQUIREMENT_QUALIFICATION_COMPARISON_TEMPLATE = """
#         You are a seasoned career advising expert in crafting resumes and cover letters.
#         You specialize in creating compelling and tailored resumes and cover letters that highlight clients skills, experiences, and achievements—meticulously aligning with the specific job descriptions they target. 
#         Your expertise extends across various industries, encompassing a deep understanding of prevailing hiring trends and Applicant Tracking Systems (ATS). 

#         Your objective is to map job requirements with the client's qualification. Take this instructions into account:

#         1. First requirements in the description are more important than the last ones and should be adressed.
#         2. If you can't find a meaningful connection, DO NOT include it in the final output.
#         3. Quantitative things like years of experience are nogotiable.
#         4. Things like 'familiarity with' or 'advanced degree' or 'is a plus'  are negotiable.
#         5. After you found a match. You have to rewrite the CV qualification to match the job description requirement language style
#         6. Try to create at least 6 matches between the job description and the cv qualification

#         Between lines, you may see examples 

#         -------
#         {examples}
#         -------

#         Pay close attention to the output instructions 

#         -------
#         {output_format_instructions}
#         -------

#         This is the cv that the client sent to you: 

#         -----
#         {cv_data}
#         -----

#         This is all the information that the client gathered about the job posting:

#         ------
#         {job_posting_data}
#         ------
#     """

class RequirementsQualificationsComparator:
    def __init__(self,
                 model_name:ModelNames,
                 user_id:int,
                 temperature:float = 0,
                 log_file_name="llm.log",
                 log_prefix="RequirementsQualificationsComparator",
                 examples:List[dict]=examples
                 ):
        self.db = DatabaseManager()
        self.logger = Logger(prefix=log_prefix,log_file_name=log_file_name).get_logger()
        self.llm_init = LLMInitializer(model_name=model_name,temperature=temperature)
        self.llm = self.llm_init.get_llm()
        self.examples_str = self._generate_examples_string(examples=examples)
        self.output_parser = JsonOutputParser(pydantic_object=RequirementsQualificationComparisonList)
        self.user_id = user_id
        self.template= PromptTemplate(
            template= REQUIREMENT_QUALIFICATION_COMPARISON_TEMPLATE,
            input_variables=["job_posting_data"],
            partial_variables={
                "output_format_instructions": self.output_parser.get_format_instructions(),
                "examples": self.examples_str,
                "parsed_worked_experiences": self._get_user_attribute(user_id=user_id,attribute="parsed_work_experiences"),
                "parsed_skills": self._get_user_attribute(user_id=user_id,attribute="parsed_skills")
            }
        )
        
        self.chain = self.template | self.llm | self.output_parser


    @staticmethod    
    def _generate_examples_string(examples:List[dict]):
        """
        Converts the example list to a string
        """
        return '\n'.join(f"EXAMPLE {index + 1}\n" + '\n'.join(f"{key}: {value}" for key, value in example.items())  
          for index, example in enumerate(examples)
        )
    
    def _get_user_attribute(self,user_id:int,attribute:str)->str:
        session = self.db.get_session()
        try:    
            user_columns = [
                    getattr(UsersModel, attr) for attr in UsersModel.__table__.columns.keys()
                    if attr in [attribute] 
                ]
            user = session.query(*user_columns).filter(UsersModel.id == user_id).first()
            user = json.dumps(user._asdict())
            return user
        except Exception as e:
            self.logger.error(f"Error getting user data: {e}")
            raise e
        finally:
            session.close()
        
    
    def _get_job_posting(self,job_id:int):
        session = self.db.get_session()
        try:
            job_posting_columns = [
                getattr(JobPostingModel, attr) for attr in JobPostingModel.__table__.columns.keys()
                if attr in ["job_posting_summary"] 
            ]
            job_posting = session.query(*job_posting_columns).filter(JobPostingModel.id == job_id).first()
            job_posting = json.dumps(job_posting._asdict())
            
            return job_posting
        except Exception as e:
            self.logger.error(f"Error getting user data: {e}")
            raise e
        finally:
            session.close()
    
    def _run_chain(self,job_posting_data:str) -> RequirementsQualificationComparisonList:
        with get_openai_callback() as cb:
            result = self.chain.invoke({"job_posting_data":job_posting_data})
            self.logger.info(f"Extracted data from text: \n {cb}")
            return result
    
    def _compare(self,job_id:int,replace_previous_comparison_flag:bool=False) -> dict:
        self.logger.info(f"Comparing requirements and qualifications for user {self.user_id} and job posting {job_id}")
        job_posting = self._get_job_posting(job_id=job_id)
        session = self.db.get_session()
        try:
            comparison = (session
                          .query(UserJobComparisonModel)
                          .filter(UserJobComparisonModel.job_posting_id == job_id,
                                  UserJobComparisonModel.user_id == self.user_id)
                          .first()
            )
            if comparison:
                if replace_previous_comparison_flag:
                    comparison.comparison = self._run_chain(job_posting_data=job_posting)
                    session.commit()
                    self.logger.info(f"Updated comparison for user {self.user_id} and job posting {job_id}")
                else:
                    self.logger.info(f"Comparison already exists for user {self.user_id} and job posting {job_id}")
            else:
                comparison = UserJobComparisonModel(job_posting_id=job_id,
                                                                        user_id=self.user_id,
                                                                        comparison=self._run_chain(job_posting_data=job_posting)
                                                                        )
                self.db.add_object(obj=comparison)
                self.logger.info(f"Added comparison for user {self.user_id} and job posting {job_id}")
        except Exception as e:
            self.logger.error(f"Error comparing requirements and qualifications: {e}")
            raise e
        finally:
            session.close()

    def compare_job_postings_with_user(self,job_ids:List[int],replace_previous_comparison_flag:bool=False):
        """Parallel implementation of the compare method"""
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_job_id = {executor.submit(self._compare, job_id, replace_previous_comparison_flag): job_id for job_id in job_ids}
            for future in as_completed(future_to_job_id):
                job_id = future_to_job_id[future]
                try:
                    result = future.result()
                except Exception as exc:
                    self.logger.error(f"An error occurred while comparing job posting {job_id}: {exc}")


if __name__ == "__main__":
    comparator = RequirementsQualificationsComparator(model_name=ModelNames.GPT3_TURBO,
                                                       user_id=1,
                                                       temperature=0)
    comparator.compare_job_postings_with_user(job_ids=[3872263836],replace_previous_comparison_flag=True)