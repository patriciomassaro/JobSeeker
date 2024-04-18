from dataclasses import dataclass
from typing import Optional
from typing import List
import json
from dataclasses import asdict
from enum import Enum

class CompanySize(Enum):
    SIZE_1_50 = ('1-50 employees', 0)
    SIZE_51_200 = ('51-200 employees', 1)
    SIZE_201_500 = ('201-500 employees', 2)
    SIZE_501_1000 = ('501-1,000 employees', 3)
    SIZE_1001_5000 = ('1,001-5,000 employees', 4)
    SIZE_5001_10000 = ('5,001-10,000 employees', 5)
    SIZE_10001_PLUS = ('10,001+ employees', 6)

    def __init__(self, text, id):
        self.text = text
        self.id = id

    @staticmethod
    def get_id(text):
        for size in CompanySize:
            if size.text == text:
                return size.id
        return None


@dataclass
class Experience:
    institution_id: int
    person: str
    position: str
    start_date: str
    end_date: Optional[str]
    job_description: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=4)

@dataclass
class Education:
    institution: str
    person: str
    degree: str
    start_date: str
    end_date: Optional[str]
    description: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=4)


@dataclass
class Person:
    name: str
    url: str
    location: Optional[str]
    about: str
    email: str
    experiences: List[Experience]
    educations: List[Education]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=4)


@dataclass
class JobPosting:
    job_id: int
    title: str
    seniority_level: str
    employment_type: str
    job_description: str
    company: str
    company_url: str
    industries: List[str]
    job_functions: List[str]
    job_salary_range_min: Optional[int]=None
    job_salary_range_max: Optional[int]=None
    job_poster_profile_url: Optional[str]=None
    job_poster_name: Optional[str]=None
    skills: Optional[List[str]]=None

    #salary min should be less than salary max if they are not null
    def __post_init__(self):
        if self.job_salary_range_min and self.job_salary_range_max:
            if self.job_salary_range_min>self.job_salary_range_max:
                raise ValueError("Salary min should be less than salary max")
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=4)
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Institution:
    name: str  # Scraped
    url:str  # Scraped
    about: str # Scraped
    website: str # Scraped
    industry: str # Scraped
    size: int # Scraped
    followers: int # Scraped
    location: Optional[str]=None # Scraped
    specialties: Optional[List[str]]=None # Scraped
    

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=4)
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JobQuery:
    url: str
    keywords: Optional[str]=None
    location: Optional[str]=None
    salary_range_id: Optional[int]=None
    time_filter_id: Optional[int]=None
    experience_level_id: Optional[int]=None
    remote_modality_id: Optional[int]=None
    company_id: Optional[int]=None
    
    def to_dict(self) -> dict:
        return asdict(self)
    


if __name__ == "__main__":
    company=Institution(
        url="https://www.linkedin.com/company/reddit-com/",
        about="Reddit is a network of more than 100,000 communities where people can dive into anything through experiences built around their interests, hobbies and passions. Reddit users submit, vote and comment on content, stories and discussions about the topics they care about the most. From pets to parenting, there’s a community for everybody on Reddit. Interested in joining our growing team? Check out redditinc.com/careers",
        industry="Software Development",
        location="San Francisco, California",
        name="Reddit",
        size="501-1000 employees",
        website="https://www.redditinc.com/",
        specialties=['Software Engineering','Full-Stack Engineering','Frontend Engineering','Backend Engineering','Social Media','Data Science','Mobile Apps,','Online Advertising']

    )

    hiring_person=Person(
        name="Xun Tang",
        about="Looking for a Staff MLE to build ML infrastructure and enable Targeting products with the economy of scale. Work from anywhere in the U.S. or Canada.",
        educations=[],
        email="",
        url="https://www.linkedin.com/in/xuntang/",
        experiences=[],
        location="San Jose, California, United States"
    )

    job_posting = JobPosting(
        title="Senior Machine Learning Engineer, Ads Prediction",
        skills=["Deep Learning", "Tensorflow", "Pytorch", "Recommendation Systems"],
        company=company,
        experience_level= " Mid-Senior",
        hiring_person=hiring_person,
        job_description= """ Reddit is a community of communities. It’s built on shared interests, passion, and trust and is home to the most open and authentic conversations on the internet. Every day, Reddit users submit, vote, and comment on the topics they care most about. With 100,000+ active communities and approximately 73+ million daily active unique visitors, Reddit is one of the internet’s largest sources of information. For more information, visit redditinc.com.

            As a company, Reddit primarily generates revenue through advertising, and we're working towards building a massive business to fund our mission. We distinguish ourselves from other digital ad platforms by attracting advertisers who want to connect with a specific target audience because of our passionate and engaged communities.

            Ads Prediction Team’s Mission Is To Predict Ads Engagement Rates Used In Auctions To Maximize Ad Engagements And Marketplace Efficiency. This Team Owns a Critical Piece In The Ads Delivery Pipeline And Machine Learning Infrastructure. Some Examples Projects

            Improve our model through model architecture engineering work including exploring different state-of-the-art model architectures
            Systematic feature engineering work to build power features from Reddit’s data with aggregation, embedding, sub-models, content understanding techniques, etc.
            Build efficient ML infrastructures and tools such as auto ML flows, batch feature engineering framework, to facilitate our ML dev efficiency


            As a Senior machine learning engineer in the Ads prediction team, you will research, formulate and execute on our mission to deliver the right ad to the right user under the right context with data and ML driven solutions.

            Your Responsibilities

            Building industrial-level models for critical ML tasks with advanced modeling techniques
            Research, implement, test, and launch new model architectures including deep neural networks with advanced pooling and feature interaction architectures
            Systematic feature engineering works to convert all kinds of raw data in Reddit (dense & sparse, behavior & content, etc) into features with various FE technologies such as aggregation, embedding, sub-models, etc. 
            Be a mentor and cross-functional advocate for the team
            Contribute meaningfully to team strategy. We give everyone a seat at the table and encourage active participation in planning for the future.


            Who You Might Be

            Tracking records of consistently driving KPI wins through systematic works around model architecture and feature engineering
            3+ years of experience with industry-level deep learning models
            3+ years of experience with mainstream ML frameworks (such as Tensorflow and Pytorch)
            4+ years of end-to-end experience of training, evaluating, testing, and deploying industry-level models
            4+ years of experience of orchestrating complicated data generation pipelines on large-scale dataset
            Experience with Ads domain is a plus
            Experience with recommendation system is a plus


            Benefits

            Comprehensive Healthcare Benefits
            401k Matching
            Workspace benefits for your home office
            Personal & Professional development funds
            Family Planning Support
            Flexible Vacation (please use them!) & Reddit Global Wellness Days
            4+ months paid Parental Leave
            Paid Volunteer time off


            Pay Transparency

            This job posting may span more than one career level.

            In addition to base salary, this job is eligible to receive equity in the form of restricted stock units, and depending on the position offered, it may also be eligible to receive a commission. Additionally, Reddit offers a wide range of benefits to U.S.-based employees, including medical, dental, and vision insurance, 401(k) program with employer match, generous time off for vacation, and parental leave. To learn more, please visit https://www.redditinc.com/careers/.

            To provide greater transparency to candidates, we share base pay ranges for all US-based job postings regardless of state. We set standard base pay ranges for all roles based on function, level, and country location, benchmarked against similar stage growth companies. Final offer amounts are determined by multiple factors including, skills, depth of work experience and relevant licenses/credentials, and may vary from the amounts listed below.

            The Base Pay Range For This Position Is

            $216,700—$303,400 USD

            Reddit is committed to providing reasonable accommodations for qualified individuals with disabilities and disabled veterans in our job application procedures. If you need assistance or an accommodation due to a disability, please contact us at ApplicationAssistance@Reddit.com.""",
        salary_range_max=303400,
        salary_range_min=216700
    )

    #write a json of the job posting
    with open("job_posting.json","w") as f:
        f.write(job_posting.to_json())
    


