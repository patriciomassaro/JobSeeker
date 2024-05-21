import json
import re
from jobseeker.llm.base_extractor import BaseLLMExtractor
from jobseeker.llm import ModelNames
from jobseeker.database import DatabaseManager 
from jobseeker.database.models import JobPosting as JobPostingModel, Institution as InstitutionModel, CompanySize as CompanySizeModel
from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

class Responsibilities(BaseModel):
    items: List[str] = Field(description="List of key job responsibilities.")


class Qualifications(BaseModel):
    experience_years: Optional[int] = Field(None, description="Required years of experience.")
    must_have: Optional[List[str]] = Field(None, description="List of must-have qualifications/experiences for the job")
    nice_to_have: Optional[List[str]] = Field(None, description="List of optional or nice to have qualifications/experiences for the job.")
    skills: List[str] = Field(description="List of essential skills for the job like technologies or programming languages. This includes soft skills")
    education: Optional[str] = Field(None, description="Minimum educational qualification required for the job.")
    
# class Compensation(BaseModel):
#     min: Optional[int] = Field(None, description="Minimum pay range for the position.")
#     mid: Optional[int] = Field(None, description="Midpoint pay range for the position.")
#     max: Optional[int] = Field(None, description="Maximum pay range for the position.")
#     additional_benefits: Optional[List[str]] = Field(None, description="List of additional benefits provided by the employer.")

class JobDescription(BaseModel):
    title: str = Field(description="Job title for the position.")
    location: str = Field(description="Geographical location or 'Remote' if applicable.")
    involved_team: Optional[str] = Field(None, description="Name of the team the job role is part of")
    seniority_level: Optional[str] = Field(None, description="Seniority level of the job role.")
    looking_for: Optional[str] = Field(None, description="what is the company looking for. Example: The team is looking for talented ML engineers to help build the next generation of AI products.")
    what_the_candidate_will_do: Optional[str] = Field(None, description="brief description of the candidate duties. Example: you will work with public data and diverse teams to build novel AI products.")
    responsibilities: Responsibilities = Field(description="Specific responsibilities associated with the job.")
    qualifications: Qualifications = Field(description="Qualifications and skills required for the job.")
    # compensation: Optional[Compensation] = Field(None, description="Compensation details including salary and benefits.")


class CompanyProfile(BaseModel):
    name: str = Field(description="Name of the company.")
    industry: Optional[str] = Field(None, description="Industry sector the company operates in.")
    size: Optional[str] = Field(None, description="Number of employees or scale of operations.")
    description: Optional[str] = Field(None, description="Brief description of the company.")
    values: Optional[List[str]] = Field(None, description="Core values of the company.")
    culture: Optional[str] = Field(None, description="Overview of the company culture.")
    headquarters: Optional[str] = Field(None, description="Location of the company's headquarters.")
    website: Optional[str] = Field(None, description="Website URL of the company.")
    mission_statement: Optional[str] = Field(None, description="The company's mission statement.")
    about: Optional[List[str]] = Field(None, description="Detailed information about the company. Including history, random facts, etc.")


class JobPosting(BaseModel):
    job_description: JobDescription = Field(description="General information about the job posting.")
    company_profile: CompanyProfile = Field(description="Information about the company offering the job.")

# Validator example within a class, to ensure pay ranges are provided correctly


class JobDescriptionLLMExtractor(BaseLLMExtractor):
    def __init__(self,
                 model_name:ModelNames,
                 temperature:float = 0,
                 log_file_name="llm.log",
                 log_prefix="JobDescriptionExtractor"
                 ):
        super().__init__(model_name=model_name, pydantic_object=JobPosting, temperature=temperature, log_prefix=log_prefix, log_file_name=log_file_name)

    def get_job_data_from_text(self,job_posting_id:id):

        session = self.db.get_session()
        try:
            job_posting_columns = [
                getattr(JobPostingModel, attr) for attr in JobPostingModel.__table__.columns.keys()
                if attr in ['title','seniority_level','employment_type','job_description','company','company_url','industries','job_functions','job_salary_range_max','job_salary_range_min','skills']
            ]
            company_columns = [
                getattr(InstitutionModel, attr) for attr in InstitutionModel.__table__.columns.keys()
                if attr in ['about','industry','specialties']
            ]
            company_sizes_columns = [
                getattr(CompanySizeModel, attr) for attr in CompanySizeModel.__table__.columns.keys()
                if attr in ['text']
            ]
            job_posting = (
                session.query(*job_posting_columns, *company_columns, *company_sizes_columns)
                .outerjoin(InstitutionModel, JobPostingModel.company_url == InstitutionModel.url)
                .outerjoin(CompanySizeModel, InstitutionModel.size == CompanySizeModel.id)
                .filter(JobPostingModel.id == job_posting_id)
                .first()
            )
            return json.dumps(job_posting._asdict())
        except Exception as e:
            self.logger.error(f"Error getting job posting data: {e}")
            raise e
        finally:
            session.close()


    def extract_job_posting_and_write_to_db(self,job_id:int,replace_existing:bool):
        self.logger.info(f"Extracting job posting {job_id}...")
        try:
            session = self.db.get_session()
            job_posting_record = session.query(JobPostingModel).filter(JobPostingModel.id == job_id).first()
            if job_posting_record:
                if replace_existing or job_posting_record.job_posting_summary is None:
                    job_posting = self.get_job_data_from_text(job_id)
                    job_description_extraction = self.extract_data_from_text(text=job_posting)
                    job_posting_record.job_posting_summary = job_description_extraction
                    session.commit()
                    self.logger.info(f"Job posting {job_id} updated successfully.")
                    return 1
                else:
                    self.logger.info(f"Job posting {job_id} already exists in the database.")
                    return 0
        except Exception as e:
            self.logger.error(f"An error occurred while updating job posting {job_posting['job_id']}: {e}")
        finally:
            session.close()

    # Using ThreadPoolExecutor to parallelize the update process
    def update_job_postings(self,job_ids:List[int],replace_existing:bool=False):
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submitting tasks to the executor
            future_to_job_posting = {executor.submit(self.extract_job_posting_and_write_to_db, job_id, replace_existing): job_id for job_id in job_ids}
            for future in as_completed(future_to_job_posting):
                job_posting = future_to_job_posting[future]
                try:
                    result = future.result()
                except Exception as exc:
                    self.logger.error(f'Job posting {job_ids} generated an exception: {exc}')
            

if __name__ == "__main__":
    job_description_extractor = JobDescriptionLLMExtractor(model_name=ModelNames.GPT3_TURBO,temperature=0)
    ids = [3872263836]
    job_description_data = job_description_extractor.update_job_postings(ids)
    
