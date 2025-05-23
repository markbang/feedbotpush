# app/database.py
from sqlmodel import create_engine, SQLModel, Session
from .core.config import settings

# This import is crucial to ensure models are registered with SQLModel.metadata
# before create_db_and_tables is called.
from . import models


engine = create_engine(settings.DATABASE_URL, echo=True)  # echo=True for debugging SQL


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
