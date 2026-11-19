import os
import sys
import tempfile
from pathlib import Path

import pytest

_tmp = tempfile.mkdtemp(prefix="helpdesk-test-")
os.environ["HELPDESK_DATABASE_URL"] = f"sqlite:///{Path(_tmp) / 'test.db'}"
os.environ["HELPDESK_MODEL_DIR"] = str(Path(_tmp) / "models")
os.environ["HELPDESK_SEED_HISTORY"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def login(client, email, password="senha123"):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin(client):
    return login(client, "admin@helpdesk.com")


@pytest.fixture(scope="session")
def tech(client):
    return login(client, "ana@helpdesk.com")


@pytest.fixture(scope="session")
def requester(client):
    return login(client, "fernanda@empresa.com")
