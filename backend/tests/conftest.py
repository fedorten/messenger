import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

from app.core.config import settings
from app.core.db import engine
from app.core.security import get_password_hash
from app.main import app
from app.models import User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        try:
            session.exec(delete(User))
            session.commit()
        except Exception:
            session.rollback()
        yield session
        try:
            session.exec(delete(User))
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    superuser = User(
        email=settings.FIRST_SUPERUSER,
        full_name="Super User",
        hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
        is_superuser=True,
    )
    db.add(superuser)
    test_user = User(
        email=settings.EMAIL_TEST_USER,
        full_name="Test User",
        hashed_password=get_password_hash("testpassword123"),
        is_superuser=False,
    )
    db.add(test_user)
    db.commit()
    
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def superuser_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    if r.status_code != 200:
        raise Exception(f"Login failed: {r.status_code} {r.text}")
    tokens = r.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture(scope="function")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    login_data = {
        "username": settings.EMAIL_TEST_USER,
        "password": "testpassword123",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}
