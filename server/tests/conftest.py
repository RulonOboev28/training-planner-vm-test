import os

os.environ["TESTING"] = "1"
os.environ["JWT_SECRET"] = "test-secret-key"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def client() -> TestClient:
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def coach_auth(client: TestClient) -> dict:
    email = "coach@example.com"
    password = "secretpass"
    client.post(
        "/auth/coach/register",
        json={"email": email, "password": password, "login": "test_coach"},
    )
    login = client.post(
        "/auth/coach/login",
        json={"login": "test_coach", "password": password},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
