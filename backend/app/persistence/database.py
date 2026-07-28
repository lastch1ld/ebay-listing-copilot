import sqlite3
from collections.abc import Callable

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

SessionFactory = Callable[[], Session]


def create_engine_for(url: str) -> Engine:
    is_sqlite_memory = url in ("sqlite:///:memory:", "sqlite://")
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
