from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.core.security import verify_password
from app.models import Users, UserCreate

from app.tests.utils.utils import random_email, random_lower_string
from app.tests.utils.user import create_random_user


def test_get_users_me(client: TestClient, user_token_headers: dict[str, str]) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["username"] == settings.FIRST_SUPERUSER


def test_get_me(client: TestClient, db: Session) -> None:
    user, username, password, name = create_random_user(db)

    login_data = {
        "username": username,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    r = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
    )
    assert 200 <= r.status_code < 300
    api_user = r.json()
    existing_user = crud.get_user_by_username(session=db, username=username)
    assert existing_user
    assert existing_user.username == api_user["username"]

    db.delete(existing_user)
    db.commit()


def test_get_me_without_auth(client: TestClient) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/users/me",
    )
    assert r.status_code == 401
    assert r.json() == {"detail": "Not authenticated"}


def test_create_user_existing_username(client: TestClient, db: Session) -> None:
    user, username, password, name = create_random_user(db)
    data = {"username": username, "password": password, "name": name}
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        json=data,
    )
    created_user = r.json()
    assert r.status_code == 400
    assert "_id" not in created_user

    db.delete(user)
    db.commit()


def test_update_user_me(client: TestClient, db: Session) -> None:
    user, username, password, old_name = create_random_user(db)

    login_data = {
        "username": username,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    new_name = "updated name"
    data = {"name": new_name}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["name"] == new_name
    db.refresh(user)

    user_query = select(Users).where(Users.username == username)
    user_db = db.exec(user_query).first()
    assert user_db
    print(user_db.username, user_db.name)
    assert user_db.username == username
    assert user_db.name == new_name

    db.delete(user)
    db.commit()


def test_update_password_me(
    client: TestClient,
    db: Session,
) -> None:
    user, username, password, name = create_random_user(db)

    login_data = {
        "username": username,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    new_password = "changethis"
    data = {
        "current_password": password,
        "new_password": new_password,
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["message"] == "Password updated successfully"

    db.refresh(user)

    user_db = db.exec(select(Users).where(Users.username == username)).first()

    assert user_db
    assert user_db.username == username
    assert verify_password(new_password, user_db.password)

    db.delete(user)
    db.commit()


def test_update_password_me_incorrect_password(client: TestClient, db: Session) -> None:
    user, username, password, name = create_random_user(db)

    login_data = {
        "username": username,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    new_password = random_lower_string()
    data = {"current_password": new_password, "new_password": new_password}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert updated_user["detail"] == "Incorrect password"

    db.delete(user)
    db.commit()


def test_update_user_me_email_exists(client: TestClient, db: Session) -> None:
    user, username, password, name = create_random_user(db)

    login_data = {
        "username": username,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    data = {"username": settings.FIRST_SUPERUSER}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
        json=data,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this username already exists"
    db.delete(user)
    db.commit()


def test_update_password_me_same_password_error(
    client: TestClient, db: Session
) -> None:
    user, username, password, name = create_random_user(db)

    login_data = {
        "username": username,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    data = {"current_password": password, "new_password": password}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json=data,
    )

    assert r.status_code == 400
    updated_user = r.json()
    assert (
        updated_user["detail"] == "New password cannot be the same as the current one"
    )
    db.delete(user)
    db.commit()


def test_delete_user_me(client: TestClient, db: Session) -> None:
    user, username, password, name = create_random_user(db)
    user_id = user.id
    login_data = {
        "username": username,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    r = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
    )
    assert r.status_code == 200
    deleted_user = r.json()
    assert deleted_user["message"] == "User deleted successfully"

    result = db.exec(select(Users).where(Users.id == user_id)).first()
    assert result is None

    user_db = crud.get_user_by_username(session=db, username=username)
    assert user_db is None

    db.delete(user)
    db.commit()


def test_delete_me_without_logging(client: TestClient, db: Session) -> None:
    user, username, password, name = create_random_user(db)

    r = client.delete(
        f"{settings.API_V1_STR}/users/me",
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authenticated"

    db.delete(user)
    db.commit()
