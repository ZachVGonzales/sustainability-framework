"""
Database connection setup using SQLAlchemy.
DB_URL is read from the .env file (or environment).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DB_URL: str = os.environ.get("DB_URL", "sqlite:///./sustainability.db")

# connect_args only needed for SQLite (to allow cross-thread usage with FastAPI)
_connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}

engine = create_engine(DB_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
