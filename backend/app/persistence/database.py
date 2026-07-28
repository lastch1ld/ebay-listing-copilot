import sqlite3
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

SessionFactory = Callable[[], Session]

_SQLITE_FILE_PREFIX = "sqlite:///"


def ensure_sqlite_directory_exists(url: str) -> None:
    if not url.startswith(_SQLITE_FILE_PREFIX):
        return
    database_path = url.removeprefix(_SQLITE_FILE_PREFIX)
    if database_path in (":memory:", ""):
        return
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)


def create_engine_for(url: str) -> Engine:
    is_sqlite_memory = url in ("sqlite:///:memory:", "sqlite://")
    ensure_sqlite_directory_exists(url)
    engine = create_engine(
        url,
        future=True,
        connect_args={"check_same_thread": False} if is_sqlite_memory else {},
        poolclass=StaticPool if is_sqlite_memory else None,
    )
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection: sqlite3.Connection, _record: object) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_session_factory(url: str) -> SessionFactory:
    engine = create_engine_for(url)
    return sessionmaker(engine, expire_on_commit=False)
