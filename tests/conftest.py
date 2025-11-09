# tests/conftest.py
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]  # корень репозитория
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["TESTING"] = "true"

from app.config import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.security import _rate_limiter  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    # Очищаем rate limiter перед каждым тестом
    _rate_limiter.clear()
    
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user():
    return {"name": "Test User", "email": "test@example.com"}


@pytest.fixture
def sample_chore():
    return {"title": "Test Chore", "cadence": "daily"}


@pytest.fixture
def sample_assignment():
    return {
        "user_id": 1,
        "chore_id": 1,
        "due_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
    }
