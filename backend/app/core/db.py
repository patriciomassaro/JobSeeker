from sqlmodel import create_engine, select, Session
from sqlalchemy.orm import sessionmaker

from app import crud
from app.core.config import settings
from app.models import (
    Users,
    UserCreate,
    InstitutionSizesEnum,
    TimeFiltersEnum,
    SeniorityLevelsEnum,
    SalaryRangeFiltersEnum,
    RemoteModalitiesEnum,
    EmploymentTypesEnum,
    ExperienceLevelsEnum,
    InstitutionSizes,
    TimeFilters,
    SeniorityLevels,
    SalaryRangeFilters,
    RemoteModalities,
    EmploymentTypes,
    ExperienceLevels,
)

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(session: Session) -> None:
    user = session.exec(
        select(Users).where(Users.username == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            name=settings.FIRST_SUPERUSER_NAME,
        )
        user = crud.create_user(session=session, user_create=user_in, is_superuser=True)

    enums = [
        InstitutionSizesEnum,
        TimeFiltersEnum,
        SeniorityLevelsEnum,
        SalaryRangeFiltersEnum,
        RemoteModalitiesEnum,
        EmploymentTypesEnum,
        ExperienceLevelsEnum,
    ]
    tables = [
        InstitutionSizes,
        TimeFilters,
        SeniorityLevels,
        SalaryRangeFilters,
        RemoteModalities,
        EmploymentTypes,
        ExperienceLevels,
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
