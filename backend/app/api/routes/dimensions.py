from typing import Any
from fastapi import APIRouter
from sqlmodel import select

from app.models import (
    ExperienceLevels,
    LLMInfo,
    LLMInfoBase,
    Dimension,
    SeniorityLevels,
    RemoteModalities,
    InstitutionSizes,
)
from app.api.deps import SessionDep

router = APIRouter()


@router.get(
    "/model-names", response_model=list[LLMInfoBase], operation_id="get_all_model_names"
)
async def get_all_model_names(session: SessionDep) -> Any:
    """
    Get available model names in the platform.
    """
    return [LLMInfoBase(**dict(row)) for row in session.exec(select(LLMInfo)).all()]


@router.get(
    "/seniority-levels",
    response_model=list[Dimension],
    operation_id="get_all_seniority_levels",
)
async def get_all_seniority_levels(session: SessionDep) -> list[Dimension]:
    """
    Get available seniority levels in the platform.
    """
    return [
        Dimension(id=row.id, description=row.description)
        for row in session.exec(select(SeniorityLevels)).all()
    ]


@router.get(
    "/remote-modalities",
    response_model=list[Dimension],
    operation_id="get_all_remote_modalities",
)
async def get_all_remote_modalities(session: SessionDep) -> list[Dimension]:
    """
    Get available employment types the platform.
    """
    return [
        Dimension(id=row.id, description=row.description)
        for row in session.exec(select(RemoteModalities)).all()
    ]


@router.get(
    "/experience-levels",
    response_model=list[Dimension],
    operation_id="get_all_experience_levels",
)
async def get_all_experience_levels(session: SessionDep) -> list[Dimension]:
    """
    Get available experience levels of the platform.
    """
    return [
        Dimension(id=row.id, description=row.description)
        for row in session.exec(select(ExperienceLevels)).all()
    ]


@router.get(
    "/institution-sizes",
    response_model=list[Dimension],
    operation_id="get_all_institution_sizes",
)
async def get_all_institution_sizes(session: SessionDep) -> list[Dimension]:
    """
    Get available employment types the platform.
    """
    return [
        Dimension(id=row.id, description=row.description)
        for row in session.exec(select(InstitutionSizes)).all()
    ]
