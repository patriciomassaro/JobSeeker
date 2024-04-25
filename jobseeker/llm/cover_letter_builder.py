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

COVER_LETTER_TEMPLATE = '''
    {{
    "context":{{
        "role" : "Career advising expert",
        "action" : "Build a cover letter based on the instructions tailored for the job based on the inputs",
        "additional info": "A colleague has already compared the job description requirements with the candidate's qualifications and provided the comparison",
        "objective" : "Generate a cover letter that will guarantee the candidate an interview by highlighting the most relevant qualifications and achievements",
        "inputs":{{
            "job_posting_data":"{job_posting_data}",
            "requirement_qualification_comparison":"{requirement_qualification_comparison}",
            "cv_data":"{cv_data}"
        }}
    }},
    "instructions":{{
        "output": " only 5 paragraphs, according to the format requirements",
        "format_requirements":{{
            "first_paragraph": {{
                "length": "2 sentences",
                "content": "Who the candidate is, what he/she wants and what he/she believes in.",
                "guidelines": {{
                    "strengths": "Emphasize strengths and mention something specific about the company if possible.",
                    "conciseness": "Be concise and clear, prioritize examples and numbers, use less words."
                }},
                "examples": [
                    "I'm a client facing solutions engineer with over 2.5 years of experience and I'd love to learn more about your growing engineering team. Over the last 12 months, I’ve helped my company generate over 100% increase in revenue by leading meetings with executive leaders and also built a variety of web applications on the side. Now I’m excited to continue my journey by contributing and growing at Adyen.",
                    "I'm a creative data scientist with 5 years of experience looking to expand my interests into blockchain after having worked on the CryptoRaiders open-source project over the past few months. Over the last 3 years, I've worked on applied ML problems in rider personalization to help increase Uber's revenue by 15 percent annually. I'm excited to bring my skills to the team at Chainlink."
                ],
            }},
            "second_paragraph": {{
                "input": "use the provided requirement_qualification_comparison",
                "content": "Pick the most relevant and impressive matches in the comparison and write a paragraph.",
                "guidelines": {{
                    "themes": "Link the qualification to the following themes: Leading People, Taking Initiative, Affinity for Challenging Work, Affinity for Different Types of Work, Affinity for Specific Work, Dealing with Failure, Managing Conflict, Driven by Curiosity",
                    "qualification": "One qualification can be linked to multiple themes",
                    "structure": "Use the theme to write a paragraph that links the qualification to the requirement.",
                    "format": "Theme --> Context --> Action --> Result",
                }},
                "link_qualification_to_theme_examples": [
                    "Conducted Feature-mapping and requirements gathering sessions with prospective and existing clients to formulate scope and backlog. Responsible for managing and creating the backlog, writing stories and acceptance criteria for all managed project --> This person likely had to ask a bunch of questions and probe for information --> Theme: Driven by curiosity",
                    "Conducted Feature-mapping and requirements gathering sessions with prospective and existing clients to formulate scope and backlog. Responsible for managing and creating the backlog, writing stories and acceptance criteria for all managed project --> This person had to do both technical work and non-technical work --> Affinity for different types of work."
                ],
                "structure_example": "Theme: Taking initiative -->I like to go above and beyond in whatever I do. Context: As one of the youngest data scientists at my startup, I had the opportunity to help investigate fraud analytics within our company's platform. Action? : Instead of just reporting my findings, I created a full company wide document pertaining to our best practices and effective ways to combat fraud after doing a week of extensive research. Result: This helped my team members respond to hundreds of client requests by just referencing the document and also helped completely pivot the company's fraud strategy."
            }},
            "third_paragraph": {{
                "input": "use the provided requirement_qualification_comparison",
                "guidelines": "same as second_paragraph, add a connection to the second_paragraph",
            }},
            "fourth_paragraph": {{
                "content": "Pick two favorite aspects about the company from the research. One value driven and one Industry-related. If the candidate uses the product, it should be first on the list.",
                "guidelines": {{
                    "honest": "Be honest about the reasons why the company appeals to the candidate.",
                    "avoid_jargon": "Avoid using jargon or buzzwords, be specific, concise and concrete.",
                    "avoid_adjectives": "Avoid adding too many adjectives or adverbs."
                }},
                "structure_examples": [
                    "I’ve been following [COMPANY] for a couple of months now and I resonate with both the company’s values and its general direction. The [Insert Value] really stands out to me because [Insert Reason]. I also recently read that [Insert topical reason] and this appeals to me because [Why it appeals to the candidate]."
                ],
            }},
            "fifth_paragraph": {{
                "content": "Simply state what the candidate wants and why.",
                "guidelines": {{
                    "conciseness": "Be concise and clear, prioritize examples and numbers, use less words.",
                    "examples": "I think you’ll find that my experience is a really good fit for [COMPANY] and specifically this position. I’m ready to take my skills to the next level with your team and look forward to hearing back.",
                }},
            }},
            "full_cover_letter_example": "I am a customer focused and creative technical account manager with 2 years of experience interested in learning more about Adyen's implementation team. Over the last two and a half years, I've helped my company generate over $10M in revenue by leading meetings with executive leaders, building a variety of web applications on the side. Now I'm excited to continue my journey by contributing and growing at Adyen. There are three things that make me the perfect fit for this position: First, I've always been curious about understanding how things work and the technology sector. As an Account manager at a machine learning startup, I wanted to push myself and understand the technical elements of my day to day. I enrolled in an online Software engineering program on the side and 2 years later, I've build multiple full stack web applications that interact with web APIs like twitter and clearbit. These technical skills that I've built up have helped me become the go-to person on my team to help debug technical issues. Second, I have plenty of experience leading meetings with high level exectuvites. I've managed delicate situations pertaining to data privacy sharing, successfully upsold additional revenue streams on the back of data analysis, and run quarterly business reviews where I've had to think quickly on my feet. As the company scaled from 50 to 250 employees, I've also taken on increased responsibility including the mentoring of junior team members. Finally, I'm excited about Adyen's vision and core values. As a global citizen that lived in 3 continents, I recognize the importance of diversity towards innovation and want to work at a company that embodies this. Having worked with multiple clients in the Fintech space over the past year, I've also become interested in payments and the opportunity to help some of the fastest growing companies in the world continue to scale. I think you will find that my experience is a good fit for Adyen and specifically this position. I'm ready to take my skills to the next level with your team and look forward to hearing back.",
        }},
    }},
    "restrictions": {{
        "format": "You must provide only 5 paragraphs according to the instructions. Do not add intros like dear hiring manager or thanks or sincerely. Just the 5 paragraphs.",
        "length": "The cover letter must be limited to 350 words.",
        "words_to_avoid": "Avoid jargon or words you usually use, avoid using adjectives or adverbs at all.",
        "quality_assurance": "The cover letter must reflect high-quality customization that aligns with the job description, demonstrating the candidate’s suitability for the role with no content repetition.",
        "things_to_avoid": "Do not use words like 'extensive','seasoned', 'advanced', 'resonate'. Do not include the name of the candidate in any paragraph."
        "explicit_connections": "Do not make the connection between the qualifications and the requirements explicit. For example, this is wrong: 'aligning perfectly with your requirement for someone who can enhance user signals and build quality lead-scoring models' "

    }}
}}
    '''


# COVER_LETTER_TEMPLATE="""
#         You are a seasoned career advising expert in crafting resumes and cover letters.
#         I will provide you with a job description, a resume data and a comparison of the job description requirements and the resume qualifications that another expert did.
#         Your objective is to build a cover letter tailored for the job. Read this instructions carefully:

#         -The letter will have 5 paragraphs
#         - DO NOT use jargon or buzzwords, be specific,concise and concrete.
#         - Not only discuss past achievements, but also how they could transfer to the new role.
        
        


#         1st paragraph: INTRODUCTION & TRANSITION
        
#             - The first paragraph must have two sentences, answering who the candidate is, what he/she wants and what he/she believes in.
#             - Emphaze strenghts and mention something specific about the company if possible.
#             - Be concise and clear, prioritize examples and nuimbers, use less words.
            
#             - The first sentence is a clear introduction. The second sentence will link to the first requirement-qualification match.

#             Example 1: I'm a client facing solutions engineer with over 2.5 years of experience and I'd love to learn more about your growing engineering team. _Over the last 12 months, I’ve helped my company generate over 100% increase in revenue by leading meetings with executive leaders and also built a variety of web applications on the side. Now I’m excited to continue my journey by contributing and growing at Adyen. 
#             Example 2: I'm a creative data scientist with 5 years of experience looking to expand my interests into blockchain after having worked on the CryptoRaiders open-source project over the past few months. Over the last 3 years, I've worked on applied ML problems in rider personalization to help increase Uber's revenue by 15 percent annually. I'm excited to bring my skills to the team at Chainlink.


#         2nd and 3rd paragraph: REQUIREMENTS-QUALIFICATION MATCH

#             The input of this processe will be this

#             ------
#             {requirement_qualification_comparison}
#             ------

#             Pick the two most relevant and impressive matches and write a paragraph for each one. The process is the following:

#             - Link the qualification to the following themes: Leading People, Taking Initiative, Affinity for Challenging Work, Affinity for Different Types of Work, Affinity for Specific Work, Dealing with Failure, Managing Conflict, Driven by Curiosity
#             - One qualification can be linked to multiple themes
#             - Use the theme to write a paragraph that links the qualification to the requirement.
#             - The structure of the paragraph is : Theme --> Context --> Action --> Result

#             Example 1: Conducted Feature-mapping and requirements gathering sessions with prospective and existing clients to formulate scope and backlog. Responsible for managing and creating the backlog, writing stories and acceptance criteria for all managed project --> This person likely had to ask a bunch of questions and probe for information --> Theme: Driven by curiosity
#                     Conducted Feature-mapping and requirements gathering sessions with prospective and existing clients to formulate scope and backlog. Responsible for managing and creating the backlog, writing stories and acceptance criteria for all managed project --> This person had to do both technical work and non-technical work --> Affinity for different types of work.

#             Structure Example: Theme: Taking initiative -->I like to go above and beyond in whatever I do. Context: As one of the youngest data scientists at my startup, I had the opportunity to help investigate fraud analytics within our company's platform.   Action? : Instead of just reporting my findings, I created a full company wide document pertaining to our best practices and effective ways to combat fraud after doing a week of extensive research. Result: This helped my team members respond to hundreds of client requests by just referencing the document and also helped completely pivot the company's fraud strategy.
                    
#             4th paragraph: WHY THE COMPANY

#             Pick two favorite aspects about the company from the research. One value driven and one Industry-related. If the candidate uses the product, it should be first on the list.

#             Example: I’ve been following [COMPANY] for a couple of months now and I resonate with both the company’s values and its general direction. The \[Insert Value] really stands out to me because \[Insert Reason]. I also recently read that [Insert topical reason] and this appeals to me because [Why it appeals to the candidate]._

#         5th paragraph: CONCLUSION

#             - Simply state what the candidate wants and why:

#             Example: I think you’ll find that my experience is a really good fit for \[COMPANY] and specifically this position. I’m ready to take my skills to the next level with your team and look forward to hearing back.
        
        
#         Here is an example of a cover letter that you can use as a reference:
#         -------
#         Dear Hiring Manager,

#         I am a customer focused and creative technical account manager with 2 years of experience interested in learning more about Adyen's implementation team. Over the last two and a half years, I've helped my company generate over $10M in revenue by leading meetings with executive leaders, building a variety of web applications on the side. Now I'm excited to continue my journey by contributing and growing at Adyen. There are three things that make me the perfect fit for this position:

#         First, I've always been curious about understanding how things work and the technology sector. As an Account manager at a machine learning startup, I wanted to push myself and understand the technical elements of my day to day. I enrolled in an online Software engineering program on the side and 2 years later, I've build multiple full stack web applications that interact with web APIs like twitter and clearbit. These technical skills that I've built up have helped me become the go-to person on my team to help debug technical issues.

#         Second, I have plenty of experience leading meetings with high level exectuvites. I've managed delicate situations pertaining to data privacy sharing, successfully upsold additional revenue streams on the back of data analysis, and run quarterly business reviews where I've had to think quickly on my feet. As the company scaled from 50 to 250 employees, I've also taken on increased responsibility including the mentoring of junior team members.

#         Finally, I'm excited about Adyen's vision and core values. As a global citizen that lived in 3 continents, I recognize the importance of diversity towards innovation and want to work at a company that embodies this. Having worked with multiple clients in the Fintech space over the past year, I've also become interested in payments and the opportunity to help some of the fastest growing companies in the world continue to scale.

#         I think you will find that my experience is a good fit for Adyen and specifically this position. I'm ready to take my skills to the next level with your team and look forward to hearing back.

#         Thanks,
#         Patricio Massaro
#         -------

#         This is the cv that the client sent to you: 

#         -----
#         {cv_data}
#         -----

#         This is all the information that the client gathered about the job posting:
#         ------
#         {job_posting_data}
#         ------


#         - LIMIT TO 350 WORDS
#         - Do not include the name of the candidate, do not include things like "dear hiring manager" or "thanks" or "sincerely". Just the 5 paragraphs
#         - AVOID JARGON OR WORDS YOU USUALLY USE
#         - AVOID ADDING TO MANY ADJECTIVES OR ADVERBS
#         - DO NOT use words like "extensive", "advanced", "resonate"
#     """



class CoverLetterBuilder(BaseBuilder):
    def __init__(self,
                 model_name:ModelNames,
                 user_id:int,
                 temperature:float = 0,
                 log_file_name="llm.log",
                 log_prefix="CVBuilder",
                 template_name="cover_letter.tex"
                 ):
        super().__init__(model_name=model_name,
                         user_id=user_id,
                         temperature=temperature,
                         log_file_name=log_file_name,
                         log_prefix=log_prefix)
        self.template_name = template_name
        self._create_chain()

    def _create_chain(self):
        self.template = PromptTemplate(
            template=COVER_LETTER_TEMPLATE,
            input_variables=["job_posting_data", "requirement_qualification_comparison"],
            partial_variables={
                "cv_data": self._get_user_summary(),
            }
        )
        self.chain = self.template | self.llm | self.output_parser

    @staticmethod
    def _update_tex_template(template, paragraphs:list[str],candidate_name:str):

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

    def _run_chain(self,job_id:int):
        with get_openai_callback() as cb:
            result = self.chain.invoke({"job_posting_data":self._get_job_summary(job_id=job_id),
                                        "requirement_qualification_comparison":self._get_comparison_summary(job_id=job_id)})
            self.logger.info(f"Built Cover Letter for user {self.user_id} and {job_id}: \n {cb}")
            return result
        
    def _build(self,job_id:int):
        self.logger.info(f"Building letter for user {self.user_id}" and f"Job {job_id}")
        letter_content = self._run_chain(job_id=job_id)
        letter_content = self._escape_latex(letter_content)
        letter_content = [line for line in letter_content.split("\n") if line != ""]        

        with open(os.path.join(ROOT_DIR, "templates", self.template_name), "r") as file:
            cover_letter_tex = self._update_tex_template(template=file.read(),
                                                        paragraphs=letter_content,
                                                        candidate_name=self._get_user_name()
                                                        )
            self._create_pdf_from_latex(latex_string=cover_letter_tex,
                                       path=os.path.join(ROOT_DIR, "media", f"{self.user_id}", f"{self._get_job_company_and_position(job_id)}_cover_letter")
                                       )
        self._cleanup_build_directory(os.path.join(ROOT_DIR, "media", f"{self.user_id}"))


if __name__ == "__main__":
    cover_letter_builder = CoverLetterBuilder(model_name=ModelNames.GPT4_TURBO, user_id=1,temperature=0.2)
    cover_letter_builder.build(job_ids=[3872266079, 3872263836])

            
            




        
