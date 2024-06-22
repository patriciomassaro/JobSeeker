from typing import Any
from fastapi import APIRouter

from app.models import AvailableLLMModels
from app.llm import ModelNames
from app.api.deps import SessionDep

router = APIRouter()


@router.get(
    "/", response_model=list[AvailableLLMModels], operation_id="get_all_model_names"
)
async def get_all_model_names(*, session: SessionDep) -> Any:
    """
    Get all model names.
    """
    models = [
        AvailableLLMModels(llm_alias=model.name, llm_value=model.value)
        for model in ModelNames
    ]
    return models
