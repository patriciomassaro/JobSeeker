from sqlalchemy.engine import create
from sqlmodel import create_engine, select, Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
import json

from app.crud.users import create_user
from app.core.config import settings
from app.models import (
    Users,
    JobPostings,
    UserCreate,
    InstitutionSizesEnum,
    TimeFiltersEnum,
    SeniorityLevelsEnum,
    SalaryRangeFiltersEnum,
    RemoteModalitiesEnum,
    EmploymentTypesEnum,
    ExperienceLevelsEnum,
    BalanceTransactionsTypeEnum,
    LLMInfoEnum,
    InstitutionSizes,
    TimeFilters,
    SeniorityLevels,
    SalaryRangeFilters,
    RemoteModalities,
    EmploymentTypes,
    ExperienceLevels,
    LLMInfo,
    BalanceTransactionsType,
)

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_pg_trgm_extension():
    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        connection.commit()


def load_job_postings_data(session: Session) -> None:
    with open(os.path.join(ROOT_PATH, "job_posting_initial_data.json")) as file:
        job_postings = json.load(file)

        for job in job_postings:
            existing_job = session.exec(
                select(JobPostings).where(JobPostings.linkedin_id == job["linkedin_id"])
            ).first()
            if not existing_job:
                session.add(JobPostings(**job))
        session.commit()


def init_db(session: Session) -> None:
    create_pg_trgm_extension()
    user = session.exec(
        select(Users).where(Users.username == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            name=settings.FIRST_SUPERUSER_NAME,
        )
        user = create_user(session=session, user_create=user_in, is_superuser=True)

    enums = [
        InstitutionSizesEnum,
        TimeFiltersEnum,
        SeniorityLevelsEnum,
        SalaryRangeFiltersEnum,
        RemoteModalitiesEnum,
        EmploymentTypesEnum,
        ExperienceLevelsEnum,
        BalanceTransactionsTypeEnum,
    ]
    tables = [
        InstitutionSizes,
        TimeFilters,
        SeniorityLevels,
        SalaryRangeFilters,
        RemoteModalities,
        EmploymentTypes,
        ExperienceLevels,
        BalanceTransactionsType,
    ]
    for enum, table in zip(enums, tables, strict=True):
        for enum_value in enum:
            exists = session.exec(
                select(table).where(table.description == enum_value.description)
            ).first()
            if not exists:
                row = table(id=enum_value.id, description=enum_value.description)
                session.add(row)
                session.commit()
                session.refresh(row)

    for enum_value in LLMInfoEnum:
        exists = session.exec(
            select(LLMInfo).where(LLMInfo.id == enum_value.value[0])
        ).first()
        if not exists:
            row = LLMInfo(
                id=enum_value.value[0],
                public_name=enum_value.value[1],
                api_name=enum_value.value[2],
                provider=enum_value.value[3],
                input_pricing=enum_value.value[4],
                output_pricing=enum_value.value[5],
            )
            session.add(row)
            session.commit()
            session.refresh(row)

    load_job_postings_data(session)
