from fastapi import APIRouter
from app.api.deps import CurrentUser, SessionDep
from app.models import InstitutionsPublic, Institutions, InstitutionPublic
from sqlmodel import select

router = APIRouter()


@router.get("/", response_model=InstitutionsPublic)
def get_institutions(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 30
):
    statement = select(Institutions).offset(skip).limit(limit)
    institutions = session.exec(statement).all()

    public_institutions = [
        InstitutionPublic.model_validate(institution) for institution in institutions
    ]
    return InstitutionsPublic(data=public_institutions)
