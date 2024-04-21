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
from jobseeker.logger import Logger

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class BaseBuilder:
    def __init__(self,
                 model_name:ModelNames,
                 user_id:int,
                 user_cv_data:dict,
                 prompt_template:str,
                 latex_template_name:str,
                 temperature:float = 0,
                 log_file_name="llm.log",
                 log_prefix="Builder",
                 user_cv_latex:str = None
        ):
        self.llm_init = LLMInitializer(model_name=model_name,temperature=temperature)
        self.llm = self.llm_init.get_llm()
        self.output_parser = StrOutputParser()
        self.cv_data = user_cv_data
        self.user_id = user_id
        if user_cv_latex is None:
            self.template= PromptTemplate(
                template= prompt_template,
                input_variables=["job_posting_data, requirement_qualification_comparison"],
                partial_variables={
                    "cv_data": self.cv_data},
            )
        else:
            self.template= PromptTemplate(
                template= prompt_template,
                input_variables=["job_posting_data, requirement_qualification_comparison"],
                partial_variables={
                    "cv_data": self.cv_data,
                    "cv_tex": user_cv_latex},
            )
        self.logger = Logger(prefix=log_prefix,log_file_name=log_file_name).get_logger()
        self.chain = self.template | self.llm | self.output_parser
        # template name should end with .tex
        if not latex_template_name.endswith(".tex") or not latex_template_name:
            raise ValueError("Template name should end with .tex")
        self.template_name = latex_template_name

    def cleanup_build_directory(self, path):
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

    
    def create_pdf_from_latex(self,latex_string, path):
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
    def escape_latex(string):
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

        # Replace each special character with its escaped version
        return ''.join(latex_special_chars.get(c, c) for c in string)