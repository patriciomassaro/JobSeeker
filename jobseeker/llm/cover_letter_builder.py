import time
import subprocess
import os
import json
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.callbacks import get_openai_callback


from jobseeker.llm import LLMInitializer, ModelNames
from jobseeker.logger import Logger

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

COVER_LETTER_TEMPLATE = """
        You are a seasoned career advising expert in crafting resumes and cover letters.
        I will provide you with a job description, a resume data and a comparison of the job description requirements and the resume qualifications that another expert did.
        Your objective is to build a cover letter tailored for the job. Read this instructions carefully:

        -The letter will have 5 paragraphs
        - DO NOT use jargon or buzzwords, be specific,concise and concrete.
        - Not only discuss past achievements, but also how they could transfer to the new role.
        -Pick 2 or 3 requirements-qualification matches from the comparison and include them in the cover letter
        
        


        1st paragraph: INTRODUCTION & TRANSITION
        
            - The first paragraph must have two sentences, answering who the candidate is, what he/she wants and what he/she believes in.
            - Emphaze strenghts and mention something specific about the company if possible.
            - Be concise and clear, prioritize examples and nuimbers, use less words.
            
            - The first sentence is a clear introduction. The second sentence will link to the first requirement-qualification match.

            Example 1: I'm a client facing solutions engineer with over 2.5 years of experience and I'd love to learn more about your growing engineering team. _Over the last 12 months, I’ve helped my company generate over 100% increase in revenue by leading meetings with executive leaders and also built a variety of web applications on the side. Now I’m excited to continue my journey by contributing and growing at Adyen. 
            Example 2: I'm a creative data scientist with 5 years of experience looking to expand my interests into blockchain after having worked on the CryptoRaiders open-source project over the past few months. Over the last 3 years, I've worked on applied ML problems in rider personalization to help increase Uber's revenue by 15 percent annually. I'm excited to bring my skills to the team at Chainlink.


        2nd and 3rd paragraph: REQUIREMENTS-QUALIFICATION MATCH

            The input of this processe will be this

            ------
            {requirement_qualification_comparison}
            ------

            Pick the two most relevant and impressive matches and write a paragraph for each one. The process is the following:

            - Link the qualification to the following themes: Leading People, Taking Initiative, Affinity for Challenging Work, Affinity for Different Types of Work, Affinity for Specific Work, Dealing with Failure, Managing Conflict, Driven by Curiosity
            - One qualification can be linked to multiple themes
            - Use the theme to write a paragraph that links the qualification to the requirement.
            - The structure of the paragraph is : Theme --> Context --> Action --> Result

            Example 1: Conducted Feature-mapping and requirements gathering sessions with prospective and existing clients to formulate scope and backlog. Responsible for managing and creating the backlog, writing stories and acceptance criteria for all managed project --> This person likely had to ask a bunch of questions and probe for information --> Theme: Driven by curiosity
                    Conducted Feature-mapping and requirements gathering sessions with prospective and existing clients to formulate scope and backlog. Responsible for managing and creating the backlog, writing stories and acceptance criteria for all managed project --> This person had to do both technical work and non-technical work --> Affinity for different types of work.

            Structure Example: Theme: Taking initiative -->I like to go above and beyond in whatever I do. Context: As one of the youngest data scientists at my startup, I had the opportunity to help investigate fraud analytics within our company's platform.   Action? : Instead of just reporting my findings, I created a full company wide document pertaining to our best practices and effective ways to combat fraud after doing a week of extensive research. Result: This helped my team members respond to hundreds of client requests by just referencing the document and also helped completely pivot the company's fraud strategy.
                    
            4th paragraph: WHY THE COMPANY

            Pick two favorite aspects about the company from the research. One value driven and one Industry-related. If the candidate uses the product, it should be first on the list.

            Example: I’ve been following [COMPANY] for a couple of months now and I resonate with both the company’s values and its general direction. The \[Insert Value] really stands out to me because \[Insert Reason]. I also recently read that [Insert topical reason] and this appeals to me because [Why it appeals to the candidate]._

        5th paragraph: CONCLUSION

            - Simply state what the candidate wants and why:

            Example: I think you’ll find that my experience is a really good fit for \[COMPANY] and specifically this position. I’m ready to take my skills to the next level with your team and look forward to hearing back.
        
        
        Here is an example of a cover letter that you can use as a reference:
        -------
        Dear Hiring Manager,

        I am a customer focused and creative technical account manager with 2 years of experience interested in learning more about Adyen's implementation team. Over the last two and a half years, I've helped my company generate over $10M in revenue by leading meetings with executive leaders, building a variety of web applications on the side. Now I'm excited to continue my journey by contributing and growing at Adyen. There are three things that make me the perfect fit for this position:

        First, I've always been curious about understanding how things work and the technology sector. As an Account manager at a machine learning startup, I wanted to push myself and understand the technical elements of my day to day. I enrolled in an online Software engineering program on the side and 2 years later, I've build multiple full stack web applications that interact with web APIs like twitter and clearbit. These technical skills that I've built up have helped me become the go-to person on my team to help debug technical issues.

        Second, I have plenty of experience leading meetings with high level exectuvites. I've managed delicate situations pertaining to data privacy sharing, successfully upsold additional revenue streams on the back of data analysis, and run quarterly business reviews where I've had to think quickly on my feet. As the company scaled from 50 to 250 employees, I've also taken on increased responsibility including the mentoring of junior team members.

        Finally, I'm excited about Adyen's vision and core values. As a global citizen that lived in 3 continents, I recognize the importance of diversity towards innovation and want to work at a company that embodies this. Having worked with multiple clients in the Fintech space over the past year, I've also become interested in payments and the opportunity to help some of the fastest growing companies in the world continue to scale.

        I think you will find that my experience is a good fit for Adyen and specifically this position. I'm ready to take my skills to the next level with your team and look forward to hearing back.

        Thanks,
        Patricio Massaro
        -------

        This is the cv that the client sent to you: 

        -----
        {cv_data}
        -----

        This is all the information that the client gathered about the job posting:
        ------
        {job_posting_data}
        ------


        - LIMIT TO 325 WORDS
        - Do not include the name of the candidate, do not include things like "dear hiring manager" or "thanks" or "sincerely". Just the 5 paragraphs
    """



class CoverLetterBuilder:
    def __init__(self,
                 model_name:ModelNames,
                 user_id:int,
                 user_cv_data:dict,
                 temperature:float = 0,
                 log_file_name="llm.log",
                 log_prefix="CoverLetterBuilder",
                 template_name: str = "cover_letter.tex",
                 ):
        self.llm_init = LLMInitializer(model_name=model_name,temperature=temperature)
        self.llm = self.llm_init.get_llm()
        self.output_parser = StrOutputParser()
        self.cv_data = user_cv_data
        self.template= PromptTemplate(
            template= COVER_LETTER_TEMPLATE,
            input_variables=["job_posting_data, requirement_qualification_comparison"],
            partial_variables={
                "cv_data": json.dumps(cv_data)},
        )
        self.logger = Logger(prefix=log_prefix,log_file_name=log_file_name).get_logger()
        self.chain = self.template | self.llm | self.output_parser
        # template name should end with .tex
        if not template_name.endswith(".tex"):
            raise ValueError("Template name should end with .tex")
        self.template_name = template_name

    
    @staticmethod
    def cleanup_build_directory(path):
        time.sleep(1)
        # Safety check: ensure directory matches expected "media/[ANYNUMBER]" pattern
        if not re.match(pattern, relative_path_component):
            print(f"Directory pattern mismatch for '{path}'. Cleanup aborted.")
            return
        
        for file in glob.glob(path+"/*"):
            if file.endswith(".pdf") or file.endswith(".tex"):
                continue
            # delete the file
            os.remove(file)

    
    @staticmethod
    def create_pdf_from_latex(latex_string, path):
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


    @staticmethod
    def update_tex_template(template, paragraphs:list[str],candidate_name:str):

    # Ensure there are exactly five paragraphs to replace the placeholders
        if len(paragraphs) != 5:
            raise ValueError("The list must contain exactly 5 paragraphs.")

        # Replace the placeholders with the corresponding paragraphs
        for i, paragraph in enumerate(paragraphs, start=1):
            placeholder = f"PARAGRAPH{i}"
            template = template.replace(placeholder, paragraph)

        # Replace the placeholder for the candidate's name
        template = template.replace("CANDIDATENAME", candidate_name)
        
        return template

    def get_letter_from_llm(self,job_data:str,requirement_qualification_comparison:str):
        self.logger.info(f"Building letter with the following data: \n {job_data} \n {requirement_qualification_comparison}")
        with get_openai_callback() as cb:
            result = self.chain.invoke({"job_posting_data":job_data,"requirement_qualification_comparison":requirement_qualification_comparison})
            self.logger.info(f"Extracted data from text: \n {cb}")
            return result

    def build_letter(self,requirement_qualification_comparison:str,job_data :str,job_id:int):
        letter_content = self.get_letter_from_llm(job_data,requirement_qualification_comparison)
        letter_content = escape_latex(letter_content)
        letter_content = [line for line in letter_escaped.split("\n") if line != ""]

        with open(os.path.join(ROOT_DIR, "templates", self.template_name), "r") as file:
            cover_letter_tex = update_tex_template(template=file.read(),
                                                   paragraphs=letter_content,
                                                   candidate_name=self.cv_data.get("profile",{}).get("name",""))
            self.create_pdf_from_latex(latex_string=cover_letter_tex,
                                       path=os.path.join(ROOT_DIR, "media", f"{self.user_id}", f"{job_id}"))
            self.cleanup_build_directory(os.path.join(ROOT_DIR, "media", f"{self.user_id}"))
            
            




        
