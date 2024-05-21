from datetime import datetime
from enum import Enum

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlmodel import Column, Field, SQLModel


# Shared propertes
# TODO replace email str with EmailStr when sqlmodel supports it
class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    name: str
    is_superuser: bool = False
    is_active: bool = True


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


# TODO replace email str with EmailStr when sqlmodel supports it
class UserRegister(SQLModel):
    username: str
    password: str
    full_name: str | None = None


# Properties to receive via API on update, all are optional
# TODO replace email str with EmailStr when sqlmodel supports it
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


# TODO replace email str with EmailStr when sqlmodel supports it
class UserUpdateMe(SQLModel):
    name: str | None = None


class UpdatePassword(SQLModel):
    current_password: str
    new_password: str


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    password: str
    resume: bytes | None = None
    parsed_personal: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_work_experiences: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_educations: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_languages: dict | None = Field(sa_column=Column(JSON), default=None)
    parsed_skills: list[str] | None = Field(
        sa_column=Column(ARRAY(String)), default=None
    )
    additional_info: str | None = None
    date_created: datetime = Field(default_factory=datetime.utcnow)
    date_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow()},
    )


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: int
    date_created: datetime
    date_updated: datetime


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


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


class FilterTimeEnum(BaseEnum):
    PAST_24_HOURS = (1, "86400")
    PAST_WEEK = (2, "604800")
    PAST_MONTH = (3, "2592000")


class FilterSalaryRangesEnum(BaseEnum):
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
