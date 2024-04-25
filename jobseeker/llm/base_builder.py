import time
import subprocess
import os
import json
import re
import glob
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.callbacks import get_openai_callback

from jobseeker.database.database_manager import DatabaseManager 
from jobseeker.database.models import (
    Users as UsersModel,
    JobPosting as JobPostingModel,
    RequirementsQualificationsComparison as RequirementsQualificationsComparisonModel
    
)


from jobseeker.llm import LLMInitializer, ModelNames
from jobseeker.logger import Logger

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class BaseBuilder:
    def __init__(self,
                 model_name:ModelNames,
                 user_id:int,
                 temperature:float = 0,
                 log_file_name="llm.log",
                 log_prefix="Builder",
        ):
        self.llm_init = LLMInitializer(model_name=model_name,temperature=temperature)
        self.llm = self.llm_init.get_llm()
        self.output_parser = StrOutputParser()
        self.user_id = user_id
        self.logger = Logger(prefix=log_prefix,log_file_name=log_file_name).get_logger()
        self.db = DatabaseManager()

    def _cleanup_build_directory(self, path):
        time.sleep(4)
        pattern = r"media/\d+"
        # Check if the path matches the expected pattern
        if not re.search(pattern, path):
            self.logger.error(f"The path does not match the expected pattern: {path}")
            raise ValueError("The path does not match the expected pattern.")

        
        for file in glob.glob(path+"/*"):
            if file.endswith(".pdf") or file.endswith(".tex"):
                continue
            # delete the file
            os.remove(file)

    def _create_pdf_from_latex(self,latex_string, path):
        # Write the LaTeX string to a file with the specified path
        directory = os.path.dirname(path)
        tex_file_path = f"{path}.tex"
        # make sure that the folder exists
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(tex_file_path, "w") as file:
            file.write(latex_string)
        
        # Run pdflatex to compile the LaTeX file into a PDF
        current_dir = os.getcwd()
        os.chdir(directory)

        process = subprocess.run(['pdflatex', '-interaction=nonstopmode', tex_file_path], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        os.chdir(current_dir)

        # Optionally, check for errors
        if process.returncode != 0:
            self.logger.error(f"Failed to compile the LaTeX file: \n {process.stdout} \n {process.stderr}")
        else:
            # Correct the print statement to reflect the actual output file name
            output_filename = f"{path}.pdf"
            self.logger.info(f"PDF created successfully: {output_filename}")

    @staticmethod
    def _escape_latex(string):
        # Mapping of LaTeX special characters that need to be escaped
        latex_special_chars = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\^{}',
            '\\': r'\textbackslash{}'
        }

        # Use a list to build the escaped string
        escaped_parts = []
        i = 0
        while i < len(string):
            if string[i] in latex_special_chars and (i == 0 or string[i - 1] != '\\'):
                # Append the escaped character if it's not already escaped
                escaped_parts.append(latex_special_chars[string[i]])
            else:
                # Append the character as is
                escaped_parts.append(string[i])
            i += 1
        return "".join(escaped_parts)
    
    def _clean_latex_code_header(self,latex_code:str)->str:
        return latex_code.replace("```latex","").replace("```tex","").replace("```","") 

    def _get_user_summary(self)->str:
        session = self.db.get_session()
        try:    
            user_columns = [
                    getattr(UsersModel, attr) for attr in UsersModel.__table__.columns.keys()
                    if attr in ["cv_summary"] 
                ]
            user = session.query(*user_columns).filter(UsersModel.id == self.user_id).first()
            user = json.dumps(user._asdict())
            return user
        except Exception as e:
            self.logger.error(f"Error getting user data: {e}")
            raise e
        finally:
            session.close()
    
    def _get_user_name(self)->str:
        session = self.db.get_session()
        try:    
            user_columns = [
                    getattr(UsersModel, attr) for attr in UsersModel.__table__.columns.keys()
                    if attr in ["name",] 
                ]
            user = session.query(*user_columns).filter(UsersModel.id == self.user_id).first()
            user = user._asdict()
            return user["name"]
        except Exception as e:
            self.logger.error(f"Error getting user data: {e}")
            raise e

    def _get_job_summary(self,job_id:int)->str:
        session = self.db.get_session()
        try:    
            job_columns = [
                    getattr(JobPostingModel, attr) for attr in JobPostingModel.__table__.columns.keys()
                    if attr in ["job_posting_summary"] 
                ]
            job = session.query(*job_columns).filter(JobPostingModel.id == job_id).first()
            job = json.dumps(job._asdict())
            return job
        except Exception as e:
            self.logger.error(f"Error getting job data: {e}")
            raise e
        finally:
            session.close()

    def _get_job_company_and_position(self,job_id:int)->str:
        session = self.db.get_session()
        try:
            job_columns = [
                    getattr(JobPostingModel, attr) for attr in JobPostingModel.__table__.columns.keys()
                    if attr in ["title","company"] 
                ]
            job = session.query(*job_columns).filter(JobPostingModel.id == job_id).first()
            job = job._asdict()
            job["company"] = job["company"].replace(" ","").replace(",","").replace("/","").replace(".","")
            job["title"] = job["title"].replace(" ","").replace(",","").replace("/","").replace(".","")
            return job["company"]+ "_" + job["title"]
        except Exception as e:
            self.logger.error(f"Error getting job data: {e}")
            raise e
        finally:
            session.close()



    def _get_comparison_summary(self,job_id:int)->str:
        session = self.db.get_session()
        try:
            comparison_columns = [
                    getattr(RequirementsQualificationsComparisonModel, attr) for attr in RequirementsQualificationsComparisonModel.__table__.columns.keys()
                    if attr in ["comparison"] 
                ]
            comparison = session.query(*comparison_columns).filter(RequirementsQualificationsComparisonModel.job_posting_id == job_id, RequirementsQualificationsComparisonModel.user_id == self.user_id).first()
            comparison = json.dumps(comparison._asdict())
            return comparison
        except Exception as e:
            self.logger.error(f"Error getting comparison data: {e}")
            raise e
        finally:
            session.close()

    def build(self, job_ids: List[int]):
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submitting tasks to the executor
            future_cv_creation = {executor.submit(self._build, job_id): job_id for job_id in job_ids}
            
            # Iterating over the completed futures
            for future in as_completed(future_cv_creation):
                job_id = future_cv_creation[future]  # Correctly retrieve the job ID using the future object
                try:
                    result = future.result()  # Attempt to get the result of the future
                    # Optionally handle the result, e.g., logging success or additional actions
                    self.logger.info(f'Successfully processed job posting {job_id} with result: {result}')
                except Exception as exc:
                    # Log the error with the specific job ID that caused the exception
                    self.logger.error(f'Job posting {job_id} generated an exception: {exc}')
