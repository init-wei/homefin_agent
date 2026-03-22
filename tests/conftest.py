import importlib

import pytest
from fastapi.testclient import TestClient


def _configure_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db_path = tmp_path / "homefin-test.db"
    monkeypatch.setenv("HOMEFIN_DATABASE_URL", f"sqlite+pysqlite:///{db_path.as_posix()}")
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

