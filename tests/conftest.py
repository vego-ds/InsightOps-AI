from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_csv_path() -> Path:
    return Path("data/sample/sales_sample.csv")
