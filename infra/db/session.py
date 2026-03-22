from functools import lru_cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from infra.config.settings import get_settings
from infra.db.base import Base


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    engine = create_engine(get_settings().database_url, future=True)
    if engine.url.get_backend_name() == "sqlite":
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(get_engine())


def session_scope() -> Session:
    return get_session_factory()()


def reset_db_state() -> None:
    get_session_factory.cache_clear()
    get_engine.cache_clear()
