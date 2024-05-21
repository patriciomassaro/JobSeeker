from langchain_core.pydantic_v1 import BaseModel, Field, validator
import json
from typing import List
import re
import os

from jobseeker.llm import ModelNames
from jobseeker.llm.base_extractor import BaseLLMExtractor
from jobseeker.llm.utils import extract_text_from_pdf_bytes
from jobseeker.database.models import Users
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import List, Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Personal(BaseModel):
    first_name: str = Field( description="Full name of the individual.")
    last_name: str = Field( description="Last name of the individual.")
    contact_number: Optional[str] = Field(None, description="Contact phone number.")
    email: Optional[str] = Field(None, description="Email address.")
    summary: Optional[str] = Field(None, description="Brief summary about the individual's professional background.")
    location: Optional[str] = Field(None, description="Location of the individual.")
    personal_links: Optional[List[str]] = Field(None, description="List of personal or professional links like github,linkedin, etc.")

    # Validate the email address
    @validator('email')
    def email_validator(cls, v):
        if v is not None:
            # it should be a valid email adress "characters@characters.characters"
            if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
                raise ValueError("Invalid email address")
        return v

class WorkExperience(BaseModel):
    title: str = Field( description="Title of the position held.")
    company_name: str = Field( description="Name of the company where the position was held.")
    start_date: str = Field( description="Start date of the employment in YYYY-MM format.")
    end_date: Optional[str] = Field(None, description="End date of the employment in YYYY-MM format, if applicable.")
    accomplishments: List[str] = Field( description="List of achievements or responsibilities in the position")

class Education(BaseModel):
    degree: str = Field( description="Name of the degree obtained.")
    institution: str = Field( description="Name of the educational institution.")
    start_date: str = Field( description="Start date of the degree program in YYYY-MM format.")
    end_date: Optional[str] = Field(None, description="End date of the degree program in YYYY-MM format, if applicable.")
    accomplishments: Optional[List[str]] = Field(None, description="List of achievements or responsibilities during studies.")

class Language(BaseModel):
    language: str = Field( description="Name of the language.")
    proficiency: str = Field( description="Level of proficiency in the language.")

class CV(BaseModel):
    personal: Personal = Field( description="Profile information of the individual.")
    work_experiences: List[WorkExperience] = Field( description="List of work experiences.")
    educations: List[Education] = Field( description="List of educational qualifications.")
    skills: List[str] = Field(description="List of any skills described in the CV.")
    languages: Optional[List[Language]] = Field(None, description="List of languages spoken and proficiency levels.")



class CVLLMExtractor(BaseLLMExtractor):
    def __init__(self,
                 model_name:str,
                 temperature:float = 0,
                 prefix="CVExtractor",
                 log_file_name="llm.log"
                 ):
        super().__init__(model_name=model_name, pydantic_object=CV, temperature=temperature, log_prefix=prefix, log_file_name=log_file_name)

    def extract_cv_and_write_to_db(self, user_id: int, replace_existing_summary: bool = False):
        self.logger.info(f"Extracting CV data for user {user_id}")
        try:
            session = self.db.get_session()
            user_record = session.query(Users).filter(Users.id == user_id).first()
            if user_record:
                # Check if the user has a resume uploaded and if we should replace the existing summary
                if user_record.resume and (replace_existing_summary or not user_record.resume_summary):
                    # Extract text from PDF data
                    cv_text = extract_text_from_pdf_bytes(user_record.resume)
                    resume_summary = self.extract_data_from_text(text=cv_text)
                    user_record.parsed_personal = resume_summary.get("personal",{})
                    user_record.parsed_work_experiences = resume_summary.get("work_experiences",{})
                    user_record.parsed_educations = resume_summary.get("educations",{})
                    user_record.parsed_skills = resume_summary.get("skills",[])
                    user_record.parsed_languages = resume_summary.get("languages",{})
                    session.commit()
                    self.logger.info(f"Successfully extracted CV data for user {user_id}")
                    return 1
                else:
                    self.logger.info(f"User {user_id} already has a CV summary or no resume uploaded. Set replace_existing_summary to True to overwrite.")
                    return 0
            else:
                self.logger.error(f"User with id {user_id} not found.")
                return 0
        except Exception as e:
            self.logger.error(f"Failed to extract CV data for user {user_id}. Error: {e}")
            raise e
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


    