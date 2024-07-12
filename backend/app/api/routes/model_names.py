from typing import Any
from fastapi import APIRouter
from sqlmodel import select

from app.models import LLMInfo, LLMInfoBase
from app.api.deps import SessionDep

router = APIRouter()


@router.get("/", response_model=list[LLMInfoBase], operation_id="get_all_model_names")
async def get_all_model_names(*, session: SessionDep) -> Any:
    """
    Get available model names in the platform.
    """
    return [LLMInfoBase(**dict(row)) for row in session.exec(select(LLMInfo)).all()]
