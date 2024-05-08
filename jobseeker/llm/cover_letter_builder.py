import os
import random
from langchain.prompts import PromptTemplate
from langchain_community.callbacks import get_openai_callback


from jobseeker.llm import ModelNames
from jobseeker.llm.base_builder import BaseBuilder
from jobseeker.logger import Logger
from jobseeker.database.models import UserJobComparison,CoverLetterParagraphs,CoverLetterParagraphsExamples

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


COVER_LETTER_TEMPLATE = '''
    {{
    "context":{{
        "role" : "Career advising expert",
        "action" : "Build a cover letter tailored for the job based on the inputs",
        "objective" : "Generate a cover letter that will guarantee the candidate an interview by highlighting the most relevant qualifications and achievements",
        "inputs":{{
            "job_posting_data":"{job_posting_data}",
            "candidate_work_experiences":"{parsed_work_experiences}",
            "candidate_education":"{parsed_educations}",
            "candidate_skills":"{parsed_skills}",
            "candidate_languages":"{parsed_languages}",
            "candidate_personal_info": "{user_additional_info}"
        }}
        "examples":"The examples will be provided for each paragraph, and will have bad outputs and their corrections.",
        "examples_use": "Use the examples as guidance, do not take them literally and DO NOT LIE. The cover letter must be tailored to the job"         
    }},
    "instructions":{{
        "output": " only 5 paragraphs, according to the format requirements",
        "format_requirements":{{
            "first_paragraph": {{
                "length": "2 sentences",
                "content": "Who the candidate is, what he/she wants and what he/she believes in. Include a transition to the second paragraph."
                "guidelines": {{
                    "strengths": "Emphasize strengths and mention something specific about the company if possible.",
                    "conciseness": "Be concise and clear, prioritize examples and numbers, use less words."
                }},
                "examples": "{first_paragraph_examples}"
            }},
            "second_paragraph": {{
                "content": "Pick the most relevant and impressive matches between the job description and the user resume and write a paragraph.",
                "link": "Link the qualification to any of the themes"
                "guidelines": {{
                    "themes": [
                        Leading People,
                        Taking Initiative,
                        Affinity for Challenging Work,
                        Affinity for Different Types of Work,
                        Dealing with Failure, 
                        Managing Conflict, 
                        Driven by Curiosity"
                    ],    
                    "qualification": "One qualification can be linked to multiple themes",
                    "structure": "Use the theme to write a paragraph that links the qualification to the requirement.",
                    "format": "Theme --> Context --> Action --> Result",
                    "structure_example": {{
                        "Theme": "Taking initiative" 
                        "intro": I like to go above and beyond in whatever I do
                        "Context": "As one of the youngest data scientists at my startup, I had the opportunity to help investigate fraud analytics within our company's platform"
                        "Action" : "Instead of just reporting my findings, I created a full company wide document pertaining to our best practices and effective ways to combat fraud after doing a week of extensive research.
                        "Result": "This helped my team members respond to hundreds of client requests by just referencing the document and also helped completely pivot the company's fraud strategy.",
                    }}
                }},
                "examples": "{second_paragraph_examples}"
            }},
            "third_paragraph": {{
                "guidelines": "same as second_paragraph",
                "examples": "{third_paragraph_examples}"
            }},
            "fourth_paragraph": {{
                "content": "Pick two favorite aspects about the company from the research. One value driven and one Industry-related. If the candidate uses the product, it should be first on the list.",
                
                "guidelines": {{
                    "personal_info": "Use the personal information provided by the user to make the cover letter more personal.",
                    "honest": "Be honest about the reasons why the company appeals to the candidate.",
                }},
                "structure_examples": [
                    "I’ve been following [COMPANY] for a couple of months now and I align with both the company’s values and its general direction. The [VALUE] really stands out to me because [REASON]."
                ],
                "examples": "{fourth_paragraph_examples}"
            }},
            "fifth_paragraph": {{
                "content": "Simply state what the candidate wants and why.",
                "guidelines": {{
                    "conciseness": "Be concise and clear, prioritize examples and numbers, use less words.",
                    "structure": "I think you’ll find that my experience is a really good fit for [COMPANY] and specifically this position. I’m ready to take my skills to the next level with your team and look forward to hearing back.",
                }},
                "examples": "{fifth_paragraph_examples}"
            }},
        }},
    }},
    "restrictions": {{
        "format": "You must provide only 5 paragraphs according to the instructions. Do not add intros like dear hiring manager or thanks or sincerely. Just the 5 paragraphs.",
        "length": "The cover letter must be limited to 250 words.",
        "action_oriented": "Make sure that the cover letter is action-oriented, focusing on measurable achievements",  
        "check_for_forbiden_words": "Using any of these words is an instant rejection: 'extensive','seasoned','appeals', 'advanced', 'resonates','spearhead','honed','efficient','ethos','keen'".
        "adverbs": "Check the letter and remove all adverbs and adjectives. Failing to do so will result in a rejection.",
        "name":  "Do not include the name of the candidate in any paragraph."
        "implicit_connections": "Show that the candidate is a good fit for the job through examples, do not say it explicitly."
    }}
}}
    '''

# COVER_LETTER_TEMPLATE = '''
#     {{
#     "context":{{
#         "role" : "Career advising expert",
#         "action" : "Build a cover letter based on the instructions tailored for the job based on the inputs",
#         "additional info": "A colleague has already compared the job description requirements with the candidate's qualifications and provided the comparison",
#         "objective" : "Generate a cover letter that will guarantee the candidate an interview by highlighting the most relevant qualifications and achievements",
#         "inputs":{{
#             "job_posting_data":"{job_posting_data}",
#             "requirement_qualification_comparison":"{requirement_qualification_comparison}",
#             "candidate_work_experiences":"{parsed_work_experiences}",
#             "candidate_education":"{parsed_educations}",
#             "candidate_skills":"{parsed_skills}",
#             "candidate_languages":"{parsed_languages}",
#             "candidate_additional_info": "{user_additional_info}"
#         }}
#         "examples":"The examples will be provided for each paragraph, and will have bad outputs and their corrections."
#     }},
#     "instructions":{{
#         "output": " only 5 paragraphs, according to the format requirements",
#         "candidate_additional_info": "Use the additional information provided by the user if it makes sense, it gives a personal touch to the cover letter.",
#         "format_requirements":{{
#             "first_paragraph": {{
#                 "length": "2 sentences",
#                 "content": "Who the candidate is, what he/she wants and what he/she believes in. Include a transition to the second paragraph."
#                 "guidelines": {{
#                     "strengths": "Emphasize strengths and mention something specific about the company if possible.",
#                     "conciseness": "Be concise and clear, prioritize examples and numbers, use less words."
#                 }},
#                 "examples": "{first_paragraph_examples}"
#             }},
#             "second_paragraph": {{
#                 "input": "use the provided requirement_qualification_comparison",
#                 "content": "Pick the most relevant and impressive matches in the comparison and write a paragraph.",
#                 "guidelines": {{
#                     "themes": "Link the qualification to the following themes: Leading People, Taking Initiative, Affinity for Challenging Work, Affinity for Different Types of Work, Affinity for Specific Work, Dealing with Failure, Managing Conflict, Driven by Curiosity",
#                     "qualification": "One qualification can be linked to multiple themes",
#                     "structure": "Use the theme to write a paragraph that links the qualification to the requirement.",
#                     "format": "Theme --> Context --> Action --> Result",
#                 }},
#                 "link_qualification_to_theme_examples": [
#                     "Conducted Feature-mapping and requirements gathering sessions with prospective and existing clients to formulate scope and backlog. Responsible for managing and creating the backlog, writing stories and acceptance criteria for all managed project --> This person likely had to ask a bunch of questions and probe for information --> Theme: Driven by curiosity",
#                     "Conducted Feature-mapping and requirements gathering sessions with prospective and existing clients to formulate scope and backlog. Responsible for managing and creating the backlog, writing stories and acceptance criteria for all managed project --> This person had to do both technical work and non-technical work --> Affinity for different types of work."
#                 ],
#                 "structure_example": "Theme: Taking initiative -->I like to go above and beyond in whatever I do. Context: As one of the youngest data scientists at my startup, I had the opportunity to help investigate fraud analytics within our company's platform. Action? : Instead of just reporting my findings, I created a full company wide document pertaining to our best practices and effective ways to combat fraud after doing a week of extensive research. Result: This helped my team members respond to hundreds of client requests by just referencing the document and also helped completely pivot the company's fraud strategy.",
#                 "examples": "{second_paragraph_examples}"
#             }},
#             "third_paragraph": {{
#                 "input": "use the provided requirement_qualification_comparison",
#                 "guidelines": "same as second_paragraph",
#                 "examples": "{third_paragraph_examples}"
#             }},
#             "fourth_paragraph": {{
#                 "content": "Pick two favorite aspects about the company from the research. One value driven and one Industry-related. If the candidate uses the product, it should be first on the list.",
#                 "guidelines": {{
#                     "honest": "Be honest about the reasons why the company appeals to the candidate.",
#                     "avoid_jargon": "Avoid using jargon or buzzwords, be specific, concise and concrete.",
#                     "avoid_adjectives": "Avoid adding too many adjectives or adverbs."
#                 }},
#                 "structure_examples": [
#                     "I’ve been following [COMPANY] for a couple of months now and I resonate with both the company’s values and its general direction. The [Insert Value] really stands out to me because [Insert Reason]. I also recently read that [Insert topical reason] and this appeals to me because [Why it appeals to the candidate]."
#                 ],
#                 "examples": "{fourth_paragraph_examples}"
#             }},
#             "fifth_paragraph": {{
#                 "content": "Simply state what the candidate wants and why.",
#                 "guidelines": {{
#                     "conciseness": "Be concise and clear, prioritize examples and numbers, use less words.",
#                     "structure": "I think you’ll find that my experience is a really good fit for [COMPANY] and specifically this position. I’m ready to take my skills to the next level with your team and look forward to hearing back.",
#                 }},
#                 "examples": "{fifth_paragraph_examples}"
#             }},
#             "full_cover_letter_example": "I am a customer focused and creative technical account manager with 2 years of experience interested in learning more about Adyen's implementation team. Over the last two and a half years, I've helped my company generate over $10M in revenue by leading meetings with executive leaders, building a variety of web applications on the side. Now I'm excited to continue my journey by contributing and growing at Adyen. There are three things that make me the perfect fit for this position: First, I've always been curious about understanding how things work and the technology sector. As an Account manager at a machine learning startup, I wanted to push myself and understand the technical elements of my day to day. I enrolled in an online Software engineering program on the side and 2 years later, I've build multiple full stack web applications that interact with web APIs like twitter and clearbit. These technical skills that I've built up have helped me become the go-to person on my team to help debug technical issues. Second, I have plenty of experience leading meetings with high level exectuvites. I've managed delicate situations pertaining to data privacy sharing, successfully upsold additional revenue streams on the back of data analysis, and run quarterly business reviews where I've had to think quickly on my feet. As the company scaled from 50 to 250 employees, I've also taken on increased responsibility including the mentoring of junior team members. Finally, I'm excited about Adyen's vision and core values. As a global citizen that lived in 3 continents, I recognize the importance of diversity towards innovation and want to work at a company that embodies this. Having worked with multiple clients in the Fintech space over the past year, I've also become interested in payments and the opportunity to help some of the fastest growing companies in the world continue to scale. I think you will find that my experience is a good fit for Adyen and specifically this position. I'm ready to take my skills to the next level with your team and look forward to hearing back.",
#         }},
#     }},
#     "restrictions": {{
#         "format": "You must provide only 5 paragraphs according to the instructions. Do not add intros like dear hiring manager or thanks or sincerely. Just the 5 paragraphs.",
#         "length": "The cover letter must be limited to 350 words.",
#         "things_to_avoid": "Do not use words like 'extensive','seasoned', 'advanced', 'resonate'. Do not include the name of the candidate in any paragraph."
#         "explicit_connections": "Do not make the connection between the qualifications and the requirements explicit. For example, this is wrong: 'aligning perfectly with your requirement for someone who can enhance user signals and build quality lead-scoring models' "

#     }}
# }}
#     '''

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
        self.examples = self._get_examples_from_db()
        self._create_chain()


    def _get_examples_from_db(self):
        with self.db as session:
            examples_dict = {}
            for i in range(1,6):
                comparison_ids = session.query(UserJobComparison.id).filter_by(user_id=self.user_id).all()
                comparison_ids = [comp_id[0] for comp_id in comparison_ids]
                examples = session.query(CoverLetterParagraphsExamples).filter(
                    CoverLetterParagraphsExamples.comparison_id.in_(comparison_ids),
                    CoverLetterParagraphsExamples.paragraph_number == i).all()
                examples= random.sample(examples,min(3,len(examples)))
                    
                examples_dict[f"paragraph_{i}"] = [
                    {"original":example.original_paragraph_text,
                     "well_done":example.edited_paragraph_text} for example in examples
                ]
        return examples_dict

    def _create_chain(self):
        self.template = PromptTemplate(
            template=COVER_LETTER_TEMPLATE,
            input_variables=["job_posting_data",
                            #  "requirement_qualification_comparison"
                             ],
            partial_variables={
                "user_additional_info": self._get_user_attribute("additional_info"),
                "parsed_work_experiences": self._get_user_attribute("parsed_work_experiences"),
                "parsed_educations": self._get_user_attribute("parsed_educations"),
                "parsed_skills": self._get_user_attribute("parsed_skills"),
                "parsed_languages": self._get_user_attribute("parsed_languages"),
                "first_paragraph_examples": self.examples["paragraph_1"],
                "second_paragraph_examples": self.examples["paragraph_2"],
                "third_paragraph_examples": self.examples["paragraph_3"],
                "fourth_paragraph_examples": self.examples["paragraph_4"],
                "fifth_paragraph_examples": self.examples["paragraph_5"]
            }
        )
        self.chain = self.template | self.llm | self.output_parser

    def _update_tex_template(self,template, paragraphs:list[str],candidate_name:str):

    # Ensure there are exactly five paragraphs to replace the placeholders
        if len(paragraphs) != 5:
            raise ValueError("The list must contain exactly 5 paragraphs.")

        # Replace the placeholders with the corresponding paragraphs
        for i, paragraph in enumerate(paragraphs, start=1):
            placeholder = f"PARAGRAPH{i}"
            template = template.replace(placeholder, self._escape_latex(paragraph))

        # Replace the placeholder for the candidate's name
        template = template.replace("CANDIDATENAME", candidate_name)
        
        return template

    def _run_chain(self,job_id:int):
        with get_openai_callback() as cb:
            result = self.chain.invoke({"job_posting_data":self._get_job_summary(job_id=job_id),
                                        "requirement_qualification_comparison":self._get_comparison_summary(job_id=job_id)})
            self.logger.info(f"Built Cover Letter for user {self.user_id} and {job_id}: \n {cb}")
            return result
        
    def _save_paragraphs_to_database(self, job_id:int, cover_letter_paragraphs:list[str]):
        if len(cover_letter_paragraphs) != 5:
            raise ValueError("The list must contain exactly 5 paragraphs.")
        with self.db as session:
            # get the comparison id
            comparison = session.query(UserJobComparison).filter_by(job_posting_id=job_id, user_id=self.user_id).first()
            if comparison:
                session.query(CoverLetterParagraphs).filter_by(comparison_id=comparison.id).delete()
                for i, paragraph in enumerate(cover_letter_paragraphs, start=1):
                    session.add(CoverLetterParagraphs(comparison_id=comparison.id, paragraph_text=paragraph, paragraph_number=i))
                session.commit()
            else:
                self.logger.error("Comparison not found in database.")

    def _save_cover_letter_to_database(self, job_id:int, pdf_bytes:bytes):
        with self.db as session:
            comparison = session.query(UserJobComparison).filter_by(job_posting_id=job_id, user_id=self.user_id).first()
            if comparison:
                comparison.cover_letter_pdf = pdf_bytes
                session.commit()
            else:
                self.logger.error("Comparison not found in database.")
        
    def _build(self,job_id:int,use_llm:bool = True):
        self.logger.info(f"Building letter for user {self.user_id}" and f"Job {job_id}")

        if use_llm:
            letter_content = self._run_chain(job_id=job_id)
            letter_content = [line for line in letter_content.split("\n") if line != ""]        
            self._save_paragraphs_to_database(job_id=job_id, cover_letter_paragraphs=letter_content)
        else:
            # Get the paragraphs from the database
            with self.db as session:
                comparison = session.query(UserJobComparison).filter_by(job_posting_id=job_id, user_id=self.user_id).first()
                if comparison:
                    paragraphs = session.query(CoverLetterParagraphs).filter_by(comparison_id=comparison.id).order_by(
                        CoverLetterParagraphs.paragraph_number).all()
                    if paragraphs:
                        letter_content = [paragraph.paragraph_text for paragraph in paragraphs]
                    else:
                        self.logger.error("There are no paragraphs")
                        raise ValueError("There are no paragraphs")
                else:
                    self.logger.error("Comparison not found in database.")
                    raise ValueError("Comparison not found in database.")
                
        
        with open(os.path.join(ROOT_DIR, "templates", self.template_name), "r") as file:
            cover_letter_tex = self._update_tex_template(template=file.read(),
                                                        paragraphs=letter_content,
                                                        candidate_name=self._get_user_attribute("name")
                                                        )
            pdf_bytes=self._create_pdf_from_latex(latex_string=cover_letter_tex,
                                                  path=os.path.join(ROOT_DIR, "media", f"{self.user_id}", f"{self._get_job_company_and_position(job_id)}_cover_letter")
                                                  )
            self._save_cover_letter_to_database(job_id=job_id, pdf_bytes=pdf_bytes)
        self._cleanup_build_directory(os.path.join(ROOT_DIR, "media", f"{self.user_id}"))


if __name__ == "__main__":
    cover_letter_builder = CoverLetterBuilder(model_name=ModelNames.GPT4_TURBO, user_id=1,temperature=0.4)
    cover_letter_builder.build(job_ids=[3872266079, 3872263836])

            
            




        

