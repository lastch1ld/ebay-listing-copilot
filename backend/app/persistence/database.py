import sqlite3
from collections.abc import Callable

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

SessionFactory = Callable[[], Session]


def create_engine_for(url: str) -> Engine:
    engine = create_engine(url, future=True)
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
