from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'event_planner.db'}")


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema() -> None:
    """Create tables and apply the small SQLite migration used by this app.

    SQLAlchemy's ``create_all`` deliberately does not add a newly introduced
    column to an existing table. This keeps existing local installations
    working when the resolved flag is introduced.
    """
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(events)")
        }
        if "resolved" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE events ADD COLUMN resolved BOOLEAN NOT NULL DEFAULT 0"
            )
