from datetime import datetime
from enum import Enum

from sqlalchemy import String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from sqlmodel import Column, Field, SQLModel, Relationship

from app.core.utils import snake_case
############# USERS #############


class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    name: str


class UserCreate(UserBase):
    password: str


class UserRegister(SQLModel):
    username: str
    password: str
    full_name: str | None = None


class UserUpdate(SQLModel):
    username: str | None = None
    name: str | None = None
    password: str | None = None
    resume: bytes | None = None
    parsed_personal: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_work_experiences: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_educations: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_languages: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_skills: list[str] | None = Field(
        sa_column=Column(ARRAY(String)), default=None
    )
    additional_info: str | None = None


class UserPublic(UserBase):
    id: int
    date_created: datetime
    date_updated: datetime


class UserPublicMe(UserPublic):
    resume: bytes | None = None
    parsed_personal: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_work_experiences: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_educations: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_languages: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_skills: list[str] | None = Field(
        sa_column=Column(ARRAY(String)), default=None
    )
    additional_info: str | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class UserUpdateMe(SQLModel):
    name: str | None = None


# Database model, database table inferred from class name
class Users(UserPublicMe, table=True):
    id: int | None = Field(default=None, primary_key=True)  # type: ignore
    password: str
    date_created: datetime = Field(default_factory=datetime.utcnow)
    date_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow()},
    )

    user_job_posting_comparisons: list["UserJobPostingComparisons"] = Relationship(
        back_populates="user"
    )


class UpdatePassword(SQLModel):
    current_password: str
    new_password: str


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: int | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str


############### ENUMS ###############


class BaseEnum(Enum):
    def __init__(self, id: int, description: str):
        self.id = id
        self.description = description

    @classmethod
    def get_id(cls, description: str) -> int | None:
        for item in cls:  # type: ignore
            if item.description == description:
                return item.id
        return None

    @classmethod
    def get_query_param(cls, value, param_name):
        """
        Get the query parameter for the given value, used to build the URL query string
        param_name: str
        value: int
        """
        for item in cls:
            if item.value == value:
                return f"{param_name}{item.value}" if item.value is not None else ""
        return ""


class InstitutionSizesEnum(BaseEnum):
    SIZE_1_50 = (0, "1-50 employees")
    SIZE_51_200 = (1, "51-200 employees")
    SIZE_201_500 = (2, "201-500 employees")
    SIZE_501_1000 = (3, "501-1,000 employees")
    SIZE_1001_5000 = (4, "1,001-5,000 employees")
    SIZE_5001_10000 = (5, "5,001-10,000 employees")
    SIZE_10001_PLUS = (6, "10,001+ employees")


class SeniorityLevelsEnum(BaseEnum):
    INTERN = (1, "intern")
    ENTRY_LEVEL = (2, "entry level")
    ASSOCIATE = (3, "associate")
    MID_SENIOR_LEVEL = (4, "mid-senior level")
    DIRECTOR = (5, "director")
    EXECUTIVE = (6, "executive")


class TimeFiltersEnum(BaseEnum):
    PAST_24_HOURS = (1, "86400")
    PAST_WEEK = (2, "604800")
    PAST_MONTH = (3, "2592000")


class SalaryRangeFiltersEnum(BaseEnum):
    RANGE_40K_PLUS = (1, "40000")
    RANGE_60K_PLUS = (2, "60000")
    RANGE_80K_PLUS = (3, "80000")
    RANGE_100K_PLUS = (4, "100000")
    RANGE_120K_PLUS = (5, "120000")
    RANGE_140K_PLUS = (6, "140000")
    RANGE_160K_PLUS = (7, "160000")
    RANGE_180K_PLUS = (8, "180000")
    RANGE_200K_PLUS = (9, "200000")


class EmploymentTypesEnum(BaseEnum):
    FULL_TIME = (1, "Full-time")
    PART_TIME = (2, "Part-time")
    CONTRACT = (3, "Contract")
    TEMPORARY = (4, "Temporary")
    INTERNSHIP = (5, "Internship")
    OTHER = (6, "Other")


class ExperienceLevelsEnum(BaseEnum):
    INTERNSHIP = (1, "Internship")
    ENTRY_LEVEL = (2, "Entry level")
    ASSOCIATE = (3, "Associate")
    MID_SENIOR_LEVEL = (4, "Mid-Senior level")
    DIRECTOR = (5, "Director")
    EXECUTIVE = (6, "Executive")


class RemoteModalitiesEnum(BaseEnum):
    ON_SITE = (1, "On-site")
    REMOTE = (2, "Remote")
    HYBRID = (3, "Hybrid")


class InstitutionSizes(SQLModel, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)
    description: str


class SeniorityLevels(SQLModel, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)
    description: str


class TimeFilters(SQLModel, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)
    description: str


class SalaryRangeFilters(SQLModel, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)
    description: str


class EmploymentTypes(SQLModel, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)
    description: str


class ExperienceLevels(SQLModel, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)
    description: str


class RemoteModalities(SQLModel, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type:ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)
    description: str


####### INSTITUTIONS ########


class InstitutionBase(SQLModel):
    name: str
    url: str
    about: str
    website: str
    industry: str
    website: str
    indsutry: str
    size: int = Field(foreign_key="institution_sizes.id")
    followers: int
    location: str | None
    specialties: list[str] | None = Field(sa_column=Column(ARRAY(String)), default=None)


class InstitutionPublic(InstitutionBase):
    pass


class InstitutionsPublic(SQLModel):
    data: list[InstitutionPublic]


class Institutions(InstitutionPublic, table=True):
    id: int = Field(default=None, primary_key=True)
    date_created: datetime = Field(default_factory=datetime.utcnow)
    date_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow()},
    )


############# JOB_Postings #############


class JobPostingBase(SQLModel):
    title: str
    company: str
    company_url: str
    location: str | None
    description: str
    seniority_level: int | None = Field(foreign_key="seniority_levels.id", default=None)
    employment_type: int | None = Field(foreign_key="employment_types.id", default=None)
    experience_level: int | None = Field(
        foreign_key="experience_levels.id", default=None
    )
    salary_range: int | None = Field(
        foreign_key="salary_range_filters.id", default=None
    )
    remote_modality: int | None = Field(
        foreign_key="remote_modalities.id", default=None
    )
    industries: list[str] | None = Field(sa_column=Column(ARRAY(String)), default=None)
    job_functions: list[str] | None = Field(
        sa_column=Column(ARRAY(String)), default=None
    )
    skills: list[str] | None = Field(sa_column=Column(ARRAY(String)), default=None)
    job_salary_min: int | None
    job_salary_max: int | None
    job_poster_name: str | None
    job_poster_profile: str | None
    summary: dict | None = Field(sa_column=Column(JSON), default=None)


class JobPostingPublic(JobPostingBase):
    pass


class JobPostingsPublic(SQLModel):
    data: list[JobPostingPublic]


class JobPostings(JobPostingPublic, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)
    date_created: datetime = Field(default_factory=datetime.utcnow)
    date_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow()},
    )

    user_job_posting_comparisons: list["UserJobPostingComparisons"] = Relationship(
        back_populates="job_posting"
    )


############# USER_JOB_POSTING_COMPARISONS #############


class UserJobPostingComparisonBase(SQLModel):
    job_posting_id: int | None = Field(foreign_key="job_postings.id")
    comparison: dict | None = Field(sa_column=Column(JSON), default=None)
    cv_pdf: bytes | None = None
    cover_letter_pdf: bytes | None = None


class UserJobPostingComparisonPublic(UserJobPostingComparisonBase):
    pass


class UserJobPostingComparisonsPublic(SQLModel):
    data: list[UserJobPostingComparisonPublic]


class UserJobPostingComparisons(UserJobPostingComparisonPublic, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)
    user_id: int | None = Field(foreign_key="users.id")
    date_created: datetime = Field(default_factory=datetime.utcnow)
    date_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow()},
    )

    user: "Users" = Relationship(back_populates="user_job_posting_comparisons")
    job_posting: "JobPostings" = Relationship(
        back_populates="user_job_posting_comparisons"
    )
    cover_letter_paragraphs: list["CoverLetterParagraphs"] = Relationship(
        back_populates="user_job_posting_comparison"
    )
    work_experiences: list["WorkExperiences"] = Relationship(
        back_populates="user_job_posting_comparison"
    )


############# PARAGRAPHS #############


class CoverLetterParagraphBase(SQLModel):
    comparison_id: int | None = Field(foreign_key="user_job_posting_comparisons.id")
    paragraph_number: int
    paragraph_text: str


class CoverLetterParagraphPublic(CoverLetterParagraphBase):
    pass


class CoverLetterParagraphsPublic(SQLModel):
    data: list[CoverLetterParagraphPublic]


class CoverLetterParagraphs(CoverLetterParagraphPublic, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)
    date_created: datetime = Field(default_factory=datetime.utcnow)
    date_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow()},
    )

    user_job_posting_comparison: "UserJobPostingComparisons" = Relationship(
        back_populates="cover_letter_paragraphs"
    )


class WorkExperienceBase(SQLModel):
    comparison_id: int | None = Field(foreign_key="user_job_posting_comparisons.id")
    start_year: int
    end_year: int | None
    title: str
    company: str
    accomplishments: list[str] | None = Field(
        sa_column=Column(ARRAY(String)), default=None
    )


class WorkExperiencePublic(WorkExperienceBase):
    pass


class WorkExperiencesPublic(SQLModel):
    data: list[WorkExperiencePublic]


class WorkExperiences(WorkExperiencePublic, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)
    date_created: datetime = Field(default_factory=datetime.utcnow)
    date_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow()},
    )
    user_job_posting_comparison: "UserJobPostingComparisons" = Relationship(
        back_populates="work_experiences"
    )


############# JOB_POSTING_QUERY #############


class JobPostingQueries(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str
    keywords: str
    location: str | None
    linkedin_company_id: int | None
    salary_range_id: int | None = Field(
        foreign_key="salary_range_filters.id", default=None
    )
    employment_type_id: int | None = Field(
        foreign_key="employment_types.id", default=None
    )
    experience_level_id: int | None = Field(
        foreign_key="experience_levels.id", default=None
    )
    remote_modality_id: int | None = Field(
        foreign_key="remote_modalities.id", default=None
    )
    time_filter_id: int | None = Field(foreign_key="time_filters.id", default=None)
