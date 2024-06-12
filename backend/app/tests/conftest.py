from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from sqlalchemy import func

from app.core.db import engine, init_db
from app.main import app
from app.tests.utils.utils import get_user_token_headers
from app.models import Users


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def user_token_headers(client: TestClient) -> dict[str, str]:
    return get_user_token_headers(client)
