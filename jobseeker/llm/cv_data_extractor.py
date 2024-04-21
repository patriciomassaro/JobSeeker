from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field, validator
import json
from typing import List
from langchain_community.callbacks import get_openai_callback
import PyPDF2
import re
import os

from jobseeker.llm import ModelNames
from jobseeker.llm.base_extractor import BaseLLMExtractor
from jobseeker.llm.utils import extract_text_from_pdf
from jobseeker.scraper.database.models import Users
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import List, Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Profile(BaseModel):
    name: str = Field( description="Full name of the individual.")
    contact_number: Optional[str] = Field(None, description="Contact phone number.")
    email: Optional[str] = Field(None, description="Email address.")
    summary: Optional[str] = Field(None, description="Brief summary about the individual's professional background.")
    address: Optional[str] = Field(None, description="Home or work address.")

    # Validate the email address
    @validator('email')
    def email_validator(cls, v):
        if v is not None:
            # it should be a valid email adress "characters@characters.characters"
            if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
                raise ValueError("Invalid email address")
        return v

class HardSkills(BaseModel):
    """
    This class represent all the relevant technologies and skills that the individual has. Examples are programming languages, frameworks, tools, etc.
    """
    name: str = Field( description="Name of the skill or technology.")
    years_of_experience: Optional[float] = Field(None, description="Number of years of experience with the skill.")

class SoftSkills(BaseModel):
    """
    This class represent all the relevant soft skills that the individual has. Examples are communication, leadership, teamwork, etc.
    """
    name: str = Field( description="Name of the soft skill.")
    proficiency: Optional[str] = Field(None, description="Level of proficiency in the skill.")


class WorkExperience(BaseModel):
    position_title: str = Field( description="Title of the position held.")
    company_name: str = Field( description="Name of the company where the position was held.")
    start_date: str = Field( description="Start date of the employment in YYYY-MM format.")
    end_date: Optional[str] = Field(None, description="End date of the employment in YYYY-MM format, if applicable.")
    accomplishments: List[str] = Field( description="List of achievements or responsibilities in the position.")

class Education(BaseModel):
    degree: str = Field( description="Name of the degree obtained.")
    institution: str = Field( description="Name of the educational institution.")
    start_date: str = Field( description="Start date of the degree program in YYYY-MM format.")
    end_date: Optional[str] = Field(None, description="End date of the degree program in YYYY-MM format, if applicable.")
    description: Optional[str] = Field(None, description="Brief description of the course or program.")
    thesis_title: Optional[str] = Field(None, description="Title of the thesis, if applicable.")

class Language(BaseModel):
    language: str = Field( description="Name of the language.")
    proficiency: str = Field( description="Level of proficiency in the language.")

class CV(BaseModel):
    profile: Profile = Field( description="Profile information of the individual.")
    experiences: List[WorkExperience] = Field( description="List of work experiences.")
    education: List[Education] = Field( description="Educational background details.")
    hard_skills: List[HardSkills] = Field(description="List of hard skills and years of experience.")
    soft_skills: List[SoftSkills] = Field(None, description="List of soft skills and proficiency levels.")
    languages: Optional[List[Language]] = Field(None, description="List of languages spoken and proficiency levels.")
    personal_links: Optional[List[HttpUrl]] = Field(None, description="List of personal or professional links.")



class CVLLMExtractor(BaseLLMExtractor):
    def __init__(self,
                 model_name:ModelNames,
                 temperature:float = 0,
                 prefix="CVExtractor",
                 log_file_name="llm.log"
                 ):
        super().__init__(model_name=model_name, pydantic_object=CV, temperature=temperature, log_prefix=prefix, log_file_name=log_file_name)

    def extract_cv_and_write_to_db(self,user_id:int):
        cv_text = extract_text_from_pdf(os.path.join(ROOT_DIR,"media",f"{user_id}", "CV.pdf"))
        cv_summary = self.extract_data_from_text(text=cv_text)
        try:
            session = self.db.get_session()
            user_record = session.query(Users).filter(Users.id == user_id).first()
            if user_record:
                user_record.cv_summary = cv_summary
                session.commit()
                self.logger.info(f"Successfully extracted CV data for user {user_id}")
                return 1
        except Exception as e:
            self.logger.error(f"Failed to extract CV data for user {user_id}. Error: {e}")
            return 0
        finally:
            session.close()
    


        

if __name__ == "__main__":
    from jobseeker.llm.utils import extract_text
    cv_text = extract_text("/Users/pmassaro/Repos/JobSeeker/jobseeker/data/cv/main.pdf")
    cv_extractor = CVLLMExtractor(model_name="gpt-3.5-turbo-0125",temperature=0)
    cv_data = cv_extractor.extract_data_from_text(cv_text)

    # Save the extracted data to a JSON file
    with open("cv_data.json", "w") as f:
        json.dump(cv_data, f, indent=4)


    