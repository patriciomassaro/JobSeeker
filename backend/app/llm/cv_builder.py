import os
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.callbacks import get_openai_callback
import random

from jobseeker.llm import ModelNames
from jobseeker.llm.base_builder import BaseBuilder
from jobseeker.logger import Logger
from jobseeker.database.models import UserJobComparison, WorkExperienceParagraphs, Users,WorkExperienceParagraphsExamples
from pydantic import BaseModel, Field
from typing import List, Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WorkExperience(BaseModel):
    title: str = Field( description="Title of the position held.")
    company_name: str = Field( description="Name of the company where the position was held.")
    start_year: str = Field( description="Start date of the employment in YYYY-MM format.")
    end_year: Optional[str] = Field(None, description="End date of the employment in YYYY-MM format, if applicable.")
    accomplishments: List[str] = Field( description="List of achievements or responsibilities in the position.")

class WorkExperiences(BaseModel):
    work_experiences: List[WorkExperience] = Field( description="List of work experiences.")

WORK_EXPERIENCE_LATEX_TEMPLATE = """
    \cventry{{{START_DATE}-{END_DATE}}}
        {{{TITLE}}}
        {{{COMPANY}}}
        {{}}
        {{}}
        {{{ACCOMPLISHMENTS}}}
"""

EDUCATION_LATEX_TEMPLATE = """
    \cventry{{{START_DATE}-{END_DATE}}}
        {{{DEGREE}}}
        {{{INSTITUTION}}}
        {{}}
        {{}}
        {{{ACCOMPLISHMENTS}}}
"""

LANGUAGE_LATEX_TEMPLATE = """
    \cvline{{{LANGUAGE}}}{{{PROFICIENCY}}}
    """

SKILLS_LATEX_TEMPLATE = """
    \section{{Skills}}
    \cvline{{}}{{{SKILLS}}}
    """

CV_PROMPT_TEMPLATE ='''
{{
    "context": {{
        "role": "Career Advisor",
        "task": "Tailor the resume to match a specific job posting",
        "goal": "Enable the client to highlight relevant experiences and skills using keywords that optimize visibility to applicant tracking systems."
    }},
    "inputs": {{
        "job_posting_data": "{job_posting_data}",
        "candidate_work_experience": "{parsed_work_experience}",
        "candidate_skills": "{parsed_skills}",
    }},
    "examples": {{
        "Explanation": "You will see how you answered in the past, and how the user corrected it. Use these examples to guide your edits but do not copy them directly.",
        "examples": {examples}
    }}
    "guidelines": {{
        "format": "Adhere to these formatting rules: {format_requirements}",
        "Preambles": "DO NOT OUTPUT ANYTHING ELSE THAN THE JSON OBJECT",
        "content": {{
            "adapt_titles": "Modify job titles to reflect those in the job posting.",
            "description_style": "Describe responsibilities and achievements using the STAR method.",
            "avoid_adjectives": "Exclude adjectives and adverbs in descriptions.",
            "focus_relevance": "Emphasize skills and experiences directly relevant to the job."
        }}
    }},
    "constraints": {{
        "experience_inclusion": "Include all work experiences.",
        "consistent_tense": "Use a consistent verb tense throughout the resume.",
        "excluded_words": ["Spearhead", "Pioneer", "Advanced"],
        "max_words_per_achievement": "Limit each achievement to 30 words."
    }}
}}
'''
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
        self.examples= self._get_examples_from_db()
        self.output_parser = JsonOutputParser(pydantic_object=WorkExperiences)
        self._create_chain()
        
        
    def _get_examples_from_db(self):
        examples_list= []
        with self.db as session:
            comparison_ids = session.query(UserJobComparison.id).filter_by(user_id=self.user_id).all()
            comparison_ids = [x[0] for x in comparison_ids]

            examples = session.query(WorkExperienceParagraphsExamples).filter(
                WorkExperienceParagraphsExamples.comparison_id.in_(comparison_ids)
            ).all()
                
            examples=random.sample(examples,min(10,len(examples)))
        
        for example in examples:
            examples_list.append(
                {
                    "original_title": example.original_title,
                    "edited_title": example.edited_title,
                    "original_accomplishments": example.original_accomplishments,
                    "edited_accomplishments": example.edited_accomplishments
                }
            )
        return examples_list
            
        
    def _load_latex_to_string(self)->str:
        with open(os.path.join(ROOT_DIR, "media", f"{self.user_id}", "CV.tex"), "r") as file:
            return file.read()
    
    def _load_template_to_string(self)->str:
        with open(os.path.join(ROOT_DIR, "templates", "CV.tex"), "r") as file:
            return file.read()
        
    def _create_chain(self):
        self.template = PromptTemplate(
            template=CV_PROMPT_TEMPLATE,
            input_variables=["job_posting_data",
                            #  "requirement_qualification_comparison"
                             ],
            partial_variables={
                "parsed_work_experience": self._get_user_attribute("parsed_work_experiences"),
                "parsed_skills": self._get_user_attribute("parsed_skills"),
                "format_requirements": self.output_parser.get_format_instructions(),
                "examples": self.examples
            }
        )
        self.chain = self.template | self.llm | self.output_parser

    def _run_chain(self,job_id:int):
        with get_openai_callback() as cb:
            result = self.chain.invoke({"job_posting_data":self._get_job_summary(job_id=job_id),
                                        # "requirement_qualification_comparison":self._get_comparison_summary(job_id=job_id)
                                        }
                                    )
            self.logger.info(f"Built CV for user {self.user_id} and {job_id} \n {cb}")
            return result
        
    def _save_cv_to_database(self, job_id:int, pdf_bytes:bytes, tex_string:str):
        with self.db as session:
            comparison = session.query(UserJobComparison).filter_by(job_posting_id=job_id, user_id=self.user_id).first()
            if comparison:
                comparison.cv_pdf = pdf_bytes
                comparison.cv_tex = tex_string
                session.commit()
            else:
                self.logger.error("Comparison not found in database.")

    def _save_work_experiences_to_database(self, job_id:int, custom_work_experiences:List[WorkExperience]):
        with self.db as session:
            comparison = session.query(UserJobComparison).filter_by(job_posting_id=job_id, user_id=self.user_id).first()
            if not comparison:
                # create the comparison
                comparison = UserJobComparison(job_posting_id=job_id, user_id=self.user_id, comparison={})
                session.add(comparison)

            session.query(WorkExperienceParagraphs).filter_by(comparison_id=comparison.id).delete()
            for work_experience in custom_work_experiences:
                work_experience_paragraph = WorkExperienceParagraphs(comparison_id=comparison.id,
                                                                        start_year=work_experience.get("start_year",""),
                                                                        end_year=work_experience.get("end_year",""),
                                                                        company=work_experience.get("company_name",""),
                                                                        title=work_experience.get("title",""),
                                                                        accomplishments=work_experience.get("accomplishments",[])
                                                                        )
                session.add(work_experience_paragraph)
            session.commit()

    def _load_personal_data_to_cv(self, template:str)->str:
        with self.db as session:
            personal_data = session.query(Users).filter_by(id=self.user_id).first().parsed_personal

            if personal_data:
                template = template.replace("FIRSTNAME", personal_data.get("first_name",""))
                template = template.replace("LASTNAME", personal_data.get("last_name",""))
                template = template.replace("MAIL", personal_data.get("email",""))
                template = template.replace("PHONE", personal_data.get("contact_number",""))
                template = template.replace("LOCATION", personal_data.get("location",""))

                personal_links_string= ""
                for personal_link in personal_data.get("personal_links",[]):
                    if "linkedin" in personal_link:
                        personal_links_string += f"\\social[linkedin][{personal_link}]{{{personal_link}}}\n"
                    elif "github" in personal_link:
                        personal_links_string += f"\\social[github][{personal_link}]{{{personal_link}}}\n"
                template = template.replace("SOCIAL", personal_links_string)
            else:
                self.logger.error("User not found in database.")
        return template
    
    def _add_education_to_cv(self, template:str)->str:
        with self.db as session:
            education_string = "\\section{Education}"
            education_data = session.query(Users).filter_by(id=self.user_id).first().parsed_educations
            if education_data:
                # sort by start date desc
                education_data = sorted(education_data, key=lambda x: x.get('start_date',''), reverse=True)
                for education in education_data:
                    if education.get('accomplishments',None):
                        accomplishments_string = "\\begin{itemize} FILL \\end{itemize}" 
                        accomplishment_items = ""
                        for accomplishment in education.get('accomplishments',[]):
                            accomplishment_items += f"\\item {self._escape_latex(accomplishment)} \n"
                        accomplishments_string = accomplishments_string.replace("FILL",accomplishment_items)
                    else:
                        accomplishments_string = ""

                    education_string += EDUCATION_LATEX_TEMPLATE.format(
                        START_DATE=education.get('start_date',''),
                        END_DATE=education.get('end_date',''),
                        DEGREE=education.get('degree',''),
                        INSTITUTION=education.get('institution',''),
                        ACCOMPLISHMENTS=accomplishments_string
                    ).replace("-None","")
            return template.replace("EDUCATIONS", education_string)

    def _add_work_experiences_to_cv(self, template:str, comparison_id:int)->str:
        with self.db as session:
            work_experiences = session.query(WorkExperienceParagraphs).filter_by(comparison_id=comparison_id).order_by(WorkExperienceParagraphs.end_year.desc(), WorkExperienceParagraphs.start_year.asc()).all()
            if work_experiences:
                work_experience_string = "\\section{Work Experience}"
                for work_experience in work_experiences:
                    if work_experience.accomplishments:
                        accomplishments_string = "\\begin{itemize} FILL \\end{itemize}"
                        accomplishment_items = ""
                        for accomplishment in work_experience.accomplishments:
                            accomplishment_items += f"\\item {self._escape_latex(accomplishment)} \n"
                        accomplishments_string = accomplishments_string.replace("FILL",accomplishment_items)
                    else:
                        accomplishments_string = ""
                    work_experience_string += WORK_EXPERIENCE_LATEX_TEMPLATE.format(
                        START_DATE=work_experience.start_year,
                        END_DATE=work_experience.end_year,
                        TITLE=work_experience.title,
                        COMPANY=work_experience.company,
                        ACCOMPLISHMENTS=accomplishments_string
                    )
            else:
                work_experience_string = ""
            return template.replace("WORKEXPERIENCES", work_experience_string)

                
        

    def _add_languages_to_cv(self, template:str)->str:
        with self.db as session:
            language_string = "\section{Languages}"
            language_data = session.query(Users).filter_by(id=self.user_id).first().parsed_languages
            if language_data:
                for language in language_data:
                    language_string += LANGUAGE_LATEX_TEMPLATE.format(
                        LANGUAGE=language.get('language',''),
                        PROFICIENCY=language.get('proficiency','')
                    )
        return template.replace("LANGUAGES", language_string)
    
    def _add_skills_to_cv(self, template:str)->str:
        with self.db as session:
            skills_string = ""
            skills_data = session.query(Users).filter_by(id=self.user_id).first().parsed_skills
            if skills_data:
                skills_string = SKILLS_LATEX_TEMPLATE.format(SKILLS=", ".join(skills_data))
        return template.replace("SKILLS", skills_string)


    def _generate_tailored_cv(self,job_id:int):
        # get the comparison
        with self.db as session:
            comparison = session.query(UserJobComparison).filter_by(job_posting_id=job_id, user_id=self.user_id).first()
            if comparison:
                latex = self._load_template_to_string()
                latex = self._load_personal_data_to_cv(template=latex)
                latex = self._add_work_experiences_to_cv(latex,comparison_id=comparison.id)
                latex = self._add_education_to_cv(latex)
                latex = self._add_languages_to_cv(latex)
                latex = self._add_skills_to_cv(latex)
                return latex
            else:
                self.logger.error("Comparison not found in database.")

    def _build(self,job_id:int, use_llm=True):
        self.logger.info(f"Building CV for user {self.user_id}" and f"Job {job_id}")
        if use_llm:
            custom_work_experiences = self._run_chain(job_id=job_id)
            custom_work_experiences = custom_work_experiences['work_experiences']
            self._save_work_experiences_to_database(job_id=job_id, custom_work_experiences=custom_work_experiences)
        custom_cv_latex= self._generate_tailored_cv(job_id=job_id)


        pdf_bytes=self._create_pdf_from_latex(latex_string=custom_cv_latex,
                                              path=os.path.join(ROOT_DIR, "media", f"{self.user_id}", f"{self._get_job_company_and_position(job_id)}_CV"))
        self._save_cv_to_database(job_id=job_id, pdf_bytes=pdf_bytes, tex_string=custom_cv_latex)
        self._cleanup_build_directory(os.path.join(ROOT_DIR, "media", f"{self.user_id}"))
            
if __name__ == "__main__":
    cv_builder = CVBuilder(model_name=ModelNames.GPT4_TURBO, user_id=1,temperature=0.3)
    cv_builder.build(job_ids=[ 3872263836])