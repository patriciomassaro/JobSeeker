from datetime import datetime
from enum import Enum

from sqlalchemy import String, TEXT
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from sqlmodel import (
    Column,
    Field,
    SQLModel,
    Relationship,
    BigInteger,
    UniqueConstraint,
)

from app.core.utils import snake_case


############# LLM NAMES #########


class ModelParameters(SQLModel):
    name: str
    temperature: float

    def __init__(self, name: str, temperature: float):
        if temperature < 0.0 or temperature > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        self.name = name
        self.temperature = temperature


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


class UserUpdateMe(SQLModel):
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


class UserPublicMe(UserBase):
    resume: bytes | None = None
    parsed_personal: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_work_experiences: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_educations: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_languages: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_skills: list[str] | None = Field(
        sa_column=Column(ARRAY(String)), default=None
    )
    additional_info: str | None = None
    balance: float = Field(default=0.0)


# Database model, database table inferred from class name
class Users(UserPublicMe, table=True):
    id: int | None = Field(default=None, primary_key=True)  # type: ignore
    password: str
    date_created: datetime = Field(default_factory=datetime.utcnow)
    date_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow()},
    )
    is_superuser: bool = False

    comparisons: list["Comparisons"] = Relationship(back_populates="user")
    llm_transactions: list["LLMTransactions"] = Relationship(back_populates="user")


class UserPassword(SQLModel):
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
    def get_id(cls, description: str | None) -> int | None:
        if description is None:
            return None
        for item in cls:  # type: ignore
            if item.description.lower() == description.lower():
                return item.id
        return None

    @classmethod
    def get_query_param(cls, value, param_name: str, value_index: int = 1) -> str:
        """
        Get the query parameter for the given value, used to build the URL query string
        param_name: str
        value: int
        """
        for item in cls:
            if item.value == value:
                return (
                    f"{param_name}{item.value[value_index]}"
                    if item.value[value_index] is not None
                    else ""
                )
        return ""


class LLMInfoEnum(Enum):
    GPT4_O = (1, "GPT4_O", "gpt-4o", "OpenAI", 5 / 1000000, 15 / 1000000)
    GPT4_TURBO = (
        2,
        "GPT4",
        "gpt-4-turbo-2024-04-09",
        "OpenAI",
        10 / 1000000,
        20 / 1000000,
    )
    GPT3_TURBO = (
        3,
        "GPT3",
        "gpt-3.5-turbo-0125",
        "OpenAI",
        0.5 / 1000000,
        1.5 / 1000000,
    )
    CLAUDE_OPUS = (
        4,
        "CLAUDE_OPUS",
        "claude-3-opus-20240229",
        "Anthropic",
        15 / 1000000,
        75 / 1000000,
    )
    CLAUDE_SONNET = (
        5,
        "CLAUDE_SONNET",
        "claude-3-5-sonnet-20240620",
        "Anthropic",
        3 / 1000000,
        15 / 1000000,
    )
    GPT4_O_MINI = (
        6,
        "GPT4_O_MINI",
        "gpt-4o-mini",
        "OpenAI",
        0.15 / 1000000,
        0.6 / 1000000,
    )


class InstitutionSizesEnum(BaseEnum):
    SIZE_2_10 = (0, "2-10 employees")
    SIZE_1_50 = (1, "11-50 employees")
    SIZE_51_200 = (2, "51-200 employees")
    SIZE_201_500 = (3, "201-500 employees")
    SIZE_501_1000 = (4, "501-1,000 employees")
    SIZE_1001_5000 = (5, "1,001-5,000 employees")
    SIZE_5001_10000 = (6, "5,001-10,000 employees")
    SIZE_10001_PLUS = (7, "10,001+ employees")


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


class LLMInfoBase(SQLModel):
    public_name: str


class LLMInfo(LLMInfoBase, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type:ignore
        return snake_case(cls.__name__)

    id: int | None = Field(default=None, primary_key=True)
    api_name: str
    provider: str
    input_pricing: float
    output_pricing: float


####### INSTITUTIONS ########


class InstitutionBase(SQLModel):
    name: str
    url: str
    about: str
    website: str
    industry: str
    website: str
    industry: str
    size_id: int = Field(foreign_key="institution_sizes.id")
    followers: int | None
    employees: int | None
    tagline: str | None
    location: str | None
    specialties: list[str] | None = Field(sa_column=Column(ARRAY(String)), default=None)


class InstitutionPublic(InstitutionBase):
    pass


class InstitutionsPublic(SQLModel):
    data: list[InstitutionPublic]


class Institutions(InstitutionBase, table=True):
    id: int = Field(default=None, primary_key=True)
    date_created: datetime = Field(default_factory=datetime.utcnow)
    date_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow()},
    )


############# JOB_Postings #############
class JobQueryParams(SQLModel):
    skip: int = 0
    limit: int = 30
    job_title: str | None = None
    company_name: str | None = None


class JobPostingBase(SQLModel):
    id: int = Field(default=None, primary_key=True)
    title: str
    company: str
    company_url: str | None
    institution_id: int | None = Field(foreign_key="institutions.id", default=None)
    location: str | None
    description: str
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
    seniority_level: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    salary_range: str | None = None
    remote_modality: str | None = None
    institution_about: str | None = None
    institution_website: str | None = None
    institution_industry: str | None = None
    institution_size: str | None = None
    institution_followers: int | None = None
    institution_employees: int | None = None
    institution_tagline: str | None = None
    institution_location: str | None = None
    institution_specialties: list[str] | None = None


class JobPostingsPublic(SQLModel):
    data: list[JobPostingPublic]


class JobPostings(JobPostingBase, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    __table_args__ = (UniqueConstraint("linkedin_id", name="uq_linkedin_id"),)

    linkedin_id: int = Field(sa_column=Column(BigInteger))
    seniority_level_id: int | None = Field(
        foreign_key="seniority_levels.id", default=None
    )
    employment_type_id: int | None = Field(
        foreign_key="employment_types.id", default=None
    )
    experience_level_id: int | None = Field(
        foreign_key="experience_levels.id", default=None
    )
    salary_range_id: int | None = Field(
        foreign_key="salary_range_filters.id", default=None
    )
    remote_modality_id: int | None = Field(
        foreign_key="remote_modalities.id", default=None
    )

    html: str = Field(sa_column=Column(TEXT))
    date_created: datetime = Field(default_factory=datetime.utcnow)
    date_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow()},
    )

    comparisons: list["Comparisons"] = Relationship(back_populates="job_posting")
    llm_transactions: list["LLMTransactions"] = Relationship(
        back_populates="job_posting"
    )


############# COMPARISONS #############


class ComparisonBase(SQLModel):
    job_posting_id: int | None = Field(foreign_key="job_postings.id")
    user_id: int | None = Field(foreign_key="users.id")
    is_active: bool = True
    id: int = Field(default=None, primary_key=True)


class CreateComparison(SQLModel):
    job_posting_id: int
    user_id: int


class ComparisonPublic(ComparisonBase):
    title: str
    location: str | None
    company: str


class ComparisonPublicDetail(ComparisonPublic):
    comparison: dict | None
    resume: str | None = None
    cover_letter: str | None = None
    work_experiences: "list[WorkExperiencePublic]"
    cover_letter_paragraphs: "list[CoverLetterParagraphPublic]"


class ComparisonsPublic(SQLModel):
    data: list[ComparisonPublic]


class Comparisons(ComparisonBase, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    comparison: dict | None = Field(sa_column=Column(JSON), default=None)
    resume: bytes | None = None
    cover_letter: bytes | None = None
    date_created: datetime = Field(default_factory=datetime.utcnow)
    date_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow()},
    )

    user: "Users" = Relationship(back_populates="comparisons")
    job_posting: "JobPostings" = Relationship(back_populates="comparisons")
    cover_letter_paragraphs: list["CoverLetterParagraphs"] = Relationship(
        back_populates="comparison"
    )
    work_experiences: list["WorkExperiences"] = Relationship(
        back_populates="comparison"
    )
    work_experience_examples: list["WorkExperienceExamples"] = Relationship(
        back_populates="comparison"
    )

    cover_letter_paragraph_examples: list["CoverLetterParagraphExamples"] = (
        Relationship(back_populates="comparison")
    )

    llm_transactions: list["LLMTransactions"] = Relationship(
        back_populates="comparison"
    )

    # The combination of user_id and job_posting_id should be unique
    __table_args__ = (
        UniqueConstraint("user_id", "job_posting_id", name="uq_user_id_job_posting_id"),
    )


############# PARAGRAPHS #############


class CoverLetterParagraphBase(SQLModel):
    comparison_id: int | None = Field(foreign_key="comparisons.id")
    paragraph_number: int
    paragraph_text: str


class CoverLetterParagraphPublic(CoverLetterParagraphBase):
    id: int
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

    comparison: "Comparisons" = Relationship(back_populates="cover_letter_paragraphs")


class WorkExperienceBase(SQLModel):
    comparison_id: int | None = Field(foreign_key="comparisons.id")
    start_year: int
    start_month: int | None
    end_year: int | None
    end_month: int | None
    title: str
    company: str
    accomplishments: list[str] | None = Field(
        sa_column=Column(ARRAY(String)), default=None
    )


class WorkExperiencePublic(WorkExperienceBase):
    id: int
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
    comparison: "Comparisons" = Relationship(back_populates="work_experiences")


############# JOB_POSTING_QUERY #############


class JobPostingQueries(SQLModel, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

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


######## WORK_EPXERIENCE_EXAMPLES ########


class WorkExperienceExampleBase(SQLModel):
    comparison_id: int | None = Field(foreign_key="comparisons.id")
    original_title: str
    original_accomplishments: list[str] | None = Field(
        sa_column=Column(ARRAY(String)), default=None
    )
    edited_title: str
    edited_accomplishments: list[str] | None = Field(
        sa_column=Column(ARRAY(String)), default=None
    )


class WorkExperienceExamples(WorkExperienceExampleBase, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)

    comparison: "Comparisons" = Relationship(back_populates="work_experience_examples")


##### Cover Letter Paragraph Examples ######


class CoverLetterParagraphExampleBase(SQLModel):
    comparison_id: int | None = Field(foreign_key="comparisons.id")
    paragraph_number: int
    original_paragraph_text: str
    edited_paragraph_text: str


class CoverLetterParagraphExamples(CoverLetterParagraphExampleBase, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int = Field(default=None, primary_key=True)

    comparison: "Comparisons" = Relationship(
        back_populates="cover_letter_paragraph_examples"
    )


###### LLM TRANSACTIONS ####


class LLMTransactions(SQLModel, table=True):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(foreign_key="users.id")
    task_name: str
    job_posting_id: int | None = Field(foreign_key="job_postings.id", default=None)
    comparison_id: int | None = Field(foreign_key="comparisons.id", default=None)
    llm_id: int = Field(foreign_key="llm_info.id")
    input_pricing: float
    output_pricing: float
    input_tokens: int
    output_tokens: int
    total_cost: float
    transaction_date: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "Users" = Relationship(back_populates="llm_transactions")
    job_posting: "JobPostings" = Relationship(back_populates="llm_transactions")
    comparison: "Comparisons" = Relationship(back_populates="llm_transactions")


class LLMTransactionTypesEnum(Enum):
    USER_CV_EXTRACTION = (1, "user_cv_extraction")
    JOB_POSTING_EXTRACTION = (2, "job_posting_extraction")
    CV_GENERATION = (3, "user_cv_generation")
    COVER_LETTER_GENERATION = (4, "cover_letter_generation")
