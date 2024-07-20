from typing import Any
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.api.decorators import require_positive_balance
import app.crud.users as crud
from app.core.utils import encode_pdf_to_base64
from app.api.deps import (
    CurrentUser,
    SessionDep,
)
from app.core.security import get_password_hash, verify_password
from app.models import (
    UserPassword,
    UserCreate,
    UserUpdateMe,
    UserPublicMe,
    Message,
    ModelParameters,
)

from app.llm.resume_data_extractor import ResumeLLMExtractor

router = APIRouter()


@router.post("/", response_model=UserPublicMe)
async def create_user(session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = crud.get_user_by_username(session=session, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)

    return user


@router.patch("/me/upload-resume", response_model=Message)
async def upload_resume(
    *, session: SessionDep, current_user: CurrentUser, file: UploadFile = File(...)
) -> Any:
    """
    Upload a resume PDF and update the user's record.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF files are allowed."
        )

    contents = await file.read()

    current_user.resume = contents
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return Message(message="Resume uploaded successfully")


@router.post("/me/add_balance", response_model=Message)
async def add_balance(*, session: SessionDep, current_user: CurrentUser, amount: float):
    ##TODO stripe?
    crud.add_balance_to_user(session=session, user=current_user, amount=amount)
    return Message(message="Balance added successfully")


@router.patch("/me", response_model=UserPublicMe)
async def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.username:
        existing_user = crud.get_user_by_username(
            session=session, username=user_in.username
        )
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this username already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
async def update_password_me(
    *, session: SessionDep, body: UserPassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.patch("/me/parse-resume", response_model=Message)
@require_positive_balance()
async def parse_resume(
    *, session: SessionDep, current_user: CurrentUser, model_in: ModelParameters
) -> Any:
    """
    Parse CV.
    """
    if not current_user:
        return HTTPException(status_code=404, detail="User not found")
    if not current_user.resume:
        raise HTTPException(status_code=400, detail="No resume uploaded")
    cv_extractor = ResumeLLMExtractor(
        model_name=model_in.name,
        temperature=model_in.temperature,
        user_id=current_user.id,  # type: ignore
    )
    cv_extractor.extract_cv_and_write_to_db()  # type: ignore

    return Message(message="Resume parsed successfully")


@router.get("/me", response_model=UserPublicMe)
async def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    if current_user.resume:
        current_user.resume = encode_pdf_to_base64(current_user.resume)  # type: ignore
    return current_user


@router.delete("/me", response_model=Message)
async def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")
