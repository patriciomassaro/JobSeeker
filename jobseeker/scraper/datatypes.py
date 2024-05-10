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
    id: int
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

