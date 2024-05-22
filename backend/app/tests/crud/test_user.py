from fastapi.encoders import jsonable_encoder
from sqlmodel import Session

from app import crud
from app.core.security import verify_password
from app.models import Users, UserCreate, UserUpdate
from app.tests.utils.utils import random_email, random_lower_string
from app.tests.utils.user import create_random_user


def test_create_user(db: Session) -> None:
    user, username, password, name = create_random_user(db)
    assert hasattr(user, "password")
    db.delete(user)
    db.commit()


def test_authenticate_user(db: Session) -> None:
    user, username, password, name = create_random_user(db)
    authenticated_user = crud.authenticate(
        session=db, username=username, password=password
    )
    assert authenticated_user
    assert user.username == authenticated_user.username

    db.delete(user)
    db.commit()


def test_not_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = crud.authenticate(session=db, username=email, password=password)
    assert user is None


def test_get_user(db: Session) -> None:
    user, username, password, name = create_random_user(db)
    user_2 = db.get(Users, user.id)
    assert user_2
    assert user.username == user_2.username
    assert jsonable_encoder(user) == jsonable_encoder(user_2)

    db.delete(user)
    db.commit()


def test_update_user(db: Session) -> None:
    user, username, password, name = create_random_user(db)
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password)
    if user.id is not None:
        crud.update_user(session=db, db_user=user, user_in=user_in_update)
    user_2 = db.get(Users, user.id)
    assert user_2
    assert user.username == user_2.username
    assert verify_password(new_password, user_2.password)
    db.delete(user)
    db.commit()
