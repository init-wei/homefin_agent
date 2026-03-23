import importlib

import pytest
from fastapi.testclient import TestClient


def _configure_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db_path = tmp_path / "homefin-test.db"
    import_dir = tmp_path / "imports"
    monkeypatch.setenv("HOMEFIN_DATABASE_URL", f"sqlite+pysqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("HOMEFIN_AUTH_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("HOMEFIN_AUTH_TOKEN_TTL_MINUTES", "60")
    monkeypatch.setenv("HOMEFIN_IMPORT_STORAGE_DIR", import_dir.as_posix())
    monkeypatch.setenv("HOMEFIN_WORKER_POLL_INTERVAL_SECONDS", "1")
    monkeypatch.setenv("HOMEFIN_OPENCLAW_CLI_COMMAND", "openclaw")
    monkeypatch.setenv("HOMEFIN_ALLOWED_WRITE_ROLES", '["owner"]')
    from infra.config.settings import get_settings
    from infra.db.session import reset_db_state

    get_settings.cache_clear()
    reset_db_state()


@pytest.fixture()
def db_session(monkeypatch: pytest.MonkeyPatch, tmp_path):
    _configure_test_env(monkeypatch, tmp_path)
    from infra.db.session import init_db, session_scope

    init_db()
    session = session_scope()
    try:
        yield session
        session.commit()
    finally:
        session.close()


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path):
    _configure_test_env(monkeypatch, tmp_path)
    import apps.api.main as api_main

    importlib.reload(api_main)
    with TestClient(api_main.app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers_factory(client: TestClient):
    counter = 0

    def _factory(*, email: str | None = None, display_name: str = "Owner", password: str = "password123"):
        nonlocal counter
        counter += 1
        resolved_email = email or f"user{counter}@example.com"
        response = client.post(
            "/auth/register",
            json={
                "email": resolved_email,
                "display_name": display_name,
                "password": password,
            },
        )
        response.raise_for_status()
        payload = response.json()
        return {"Authorization": f"Bearer {payload['access_token']}"}, payload["user"]

    return _factory
