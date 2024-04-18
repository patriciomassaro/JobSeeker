import json
from jobseeker.llm.base_extractor import BaseLLMExtractor
from jobseeker.llm import ModelNames
from pydantic import BaseModel, EmailStr, HttpUrl, Field, validator
from typing import List, Optional

class JobDescription(BaseModel):
    title: str = Field(description="Job title for the position.")
    location: str = Field(description="Geographical location or 'Remote' if applicable.")
    remote: Optional[bool] = Field(None, description="Indicates whether the job is remote.")
    pay_range: Optional[str] = Field(None, description="Descriptive salary range for the job.")

    @validator('pay_range')
    def pay_range_validator(cls, v):
        if v and not re.match(r"Min: \$(\d+), Mid: \$(\d+), Max: \$(\d+)", v):
            raise ValueError("Pay range should be formatted as 'Min: $X, Mid: $Y, Max: $Z'")
        return v

class Responsibilities(BaseModel):
    items: List[str] = Field(description="List of key job responsibilities.")


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

class Qualifications(BaseModel):
    experience_years: Optional[int] = Field(None, description="Required years of experience.")
    required_skills: List[str] = Field(description="List of essential skills for the job.")
    additional_skills: Optional[List[str]] = Field(None, description="List of additional skills that are beneficial but not mandatory.")

class Compensation(BaseModel):
    base_pay: Optional[str] = Field(None, description="Base pay range for the position.")
    additional_benefits: Optional[List[str]] = Field(None, description="List of additional benefits provided by the employer.")

class JobPosting(BaseModel):
    job_description: JobDescription = Field(description="General information about the job posting.")
    responsibilities: Responsibilities = Field(description="Specific responsibilities associated with the job.")
    company_profile: CompanyProfile = Field(description="Information about the company offering the job.")
    qualifications: Qualifications = Field(description="Qualifications and skills required for the job.")
    compensation: Optional[Compensation] = Field(None, description="Compensation details including salary and benefits.")

# Validator example within a class, to ensure pay ranges are provided correctly


class JobDescriptionLLMExtractor(BaseLLMExtractor):
    def __init__(self,
                 model_name:ModelNames,
                 temperature:float = 0,
                 log_file_name="llm.log",
                 log_prefix="JobDescriptionExtractor"
                 ):
        super().__init__(model_name=model_name, pydantic_object=JobPosting, temperature=temperature, log_prefix=log_prefix, log_file_name=log_file_name)
        

if __name__ == "__main__":
    from jobseeker.llm.utils import extract_text
    job_description_extractor = JobDescriptionLLMExtractor(model_name="gpt-3.5-turbo-0125",temperature=0)
    text = """
    Affirm is reinventing credit to make it more honest and friendly, giving consumers the flexibility to buy now and pay later without any hidden fees or compounding interest.

        Join the Affirm team as a Machine Learning Engineer II and contribute to the success of our ML Underwriting team. We are the driving force behind Affirm's core value proposition, leveraging cutting-edge machine learning to assess creditworthiness throughout the life cycle of loan applications.

        As a Machine Learning Engineer on our team, you will be at the forefront of developing high-quality, production-ready models that play a central role in our decision-making processes. Your contributions will be instrumental in shaping our financial landscape. If you have a strong interest in machine learning and enjoy challenging work, Affirm is the place for you!

        What you'll do


        - Use Affirm’s proprietary and other third party data to develop machine learning models that predict the likelihood of default and make an approval or decline decision to achieve business objectives
        - Partner with platform and product engineering teams to build model training, decisioning, and monitoring systems
        - Research ground breaking solutions and develop prototypes that drive the future of credit decisioning at Affirm
        - Implement and scale data pipelines, new features, and algorithms that are essential to our production models
        - Collaborate with the engineering, credit, and product teams to define requirements for new products

        What we look for


        - 2+ years of experience as a machine learning engineer or PhD in a relevant field
        - Proficiency in machine learning with experience in areas such as Generalized Linear Models, Gradient Boosting, Deep Learning, and Probabilistic Calibration. Domain knowledge in credit risk is a plus
        - Strong engineering skills in Python and data manipulation skills like SQL
        - Experience using large scale distributed systems like Spark or Ray
        - Experience using open source projects and software such as scikit-learn, pandas, NumPy, XGBoost, Kubeflow
        - Experience developing machine learning models at scale from inception to business impact
        - Excellent written and oral communication skills and the capability to drive cross-functional requirements with product and engineering teams
        - The ability to present technical concepts and results in an audience-appropriate way
        - Persistence, patience and a strong sense of responsibility – we build the decision making that enables consumers and partners to place their trust in Affirm!

        Pay Grade - USA 29


        Employees new to Affirm or promoted into a new role, typically begin in the min to mid range.


        USA base pay range (CA, WA, NY, NJ, CT) per year:


        Min: $138,800

        Mid: $173,500

        Max: $208,200

        USA base pay range (all other U.S. states) per year:


        Min: $124,900

        Mid: $156,100

        Max: $187,300

        Location: Remote - US


        Affirm is proud to be a remote-first company! The majority of our roles are remote and you can work almost anywhere within the country of employment. Affirmers in proximal roles have the flexibility to work remotely, but will occasionally be required to work out of their assigned Affirm office. A limited number of roles remain office-based due to the nature of their job responsibilities.

        Benefits


        We’re extremely proud to offer competitive benefits that are anchored to our core value of people come first. Some key highlights of our benefits package include:

        - Health care coverage - Affirm covers all premiums for all levels of coverage for you and your dependents
        - Flexible Spending Wallets - generous stipends for spending on Technology, Food, various Lifestyle needs, and family forming expenses
        - Time off - competitive vacation and holiday schedules allowing you to take time off to rest and recharge
        - ESPP - An employee stock purchase plan enabling you to buy shares of Affirm at a discount

        We believe It’s On Us to provide an inclusive interview experience for all, including people with disabilities. We are happy to provide reasonable accommodations to candidates in need of individualized support during the hiring process.

        [For U.S. positions that could be performed in Los Angeles or San Francisco] Pursuant to the San Francisco Fair Chance Ordinance and Los Angeles Fair Chance Initiative for Hiring Ordinance, Affirm will consider for employment qualified applicants with arrest and conviction records.

        By clicking "Submit Application," you acknowledge that you have read the Affirm Employment Privacy Policy for applicants within the United States, the EU Employee Notice Regarding Use of Personal Data (Poland) for applicants applying from Poland, the EU Employee Notice Regarding Use of Personal Data (Spain) for applicants applying from Spain, or the Affirm U.K. Limited Employee Notice Regarding Use of Personal Data for applicants applying from the United Kingdom, and hereby freely and unambiguously give informed consent to the collection, processing, use, and storage of your personal information as described therein.
    """
    job_description_data = job_description_extractor.extract_data_from_text(text)
    # Save the extracted data to a JSON file
    with open("job_data.json", "w") as f:
        json.dump(job_description_data, f, indent=4)
    
