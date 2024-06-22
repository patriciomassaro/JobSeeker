from typing import Any
from fastapi import APIRouter, HTTPException, UploadFile, File
from app import crud
from app.core.utils import encode_pdf_to_base64
from app.api.deps import (
    CurrentUser,
    SessionDep,
)
from app.core.security import get_password_hash, verify_password
from app.models import (
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserUpdate,
    UserPublicMe,
    Message,
    ModelParameters,
)

from app.llm.cv_data_extractor import CVLLMExtractor

router = APIRouter()


@router.post("/", response_model=UserPublic)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
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


@router.post("/me/upload-resume", response_model=Message)
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

    print(contents)
    current_user.resume = contents
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return Message(message="Resume uploaded successfully")


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdate, current_user: CurrentUser
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
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
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
def parse_resume(
    *, session: SessionDep, current_user: CurrentUser, model_in: ModelParameters
) -> Any:
    """
    Parse CV.
    """
    if not current_user:
        return HTTPException(status_code=404, detail="User not found")
    if not current_user.resume:
        raise HTTPException(status_code=400, detail="No resume uploaded")
    cv_extractor = CVLLMExtractor(
        model_name=model_in.get_value(), temperature=model_in.temperature
    )
    cv_extractor.extract_cv_and_write_to_db(user_id=current_user.id)  # type: ignore

    return Message(message="Resume parsed successfully")


@router.get("/me", response_model=UserPublicMe)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    if current_user.resume:
        current_user.resume = encode_pdf_to_base64(current_user.resume)
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")
