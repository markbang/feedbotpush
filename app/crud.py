# app/crud.py
from sqlmodel import Session, select, and_  # Added and_
from datetime import datetime, timezone, timedelta, date
from typing import List
from . import models, schemas


def create_feedback_db(
    session: Session, feedback_in: schemas.UserFeedbackCreate
) -> models.UserFeedback:
    """
    Creates a new feedback entry in the database.
    The created_at field is set to current UTC+8 time and stored as a naive datetime.
    """
    db_feedback = models.UserFeedback.model_validate(feedback_in)

    # Define UTC+8 timezone
    utc_plus_8 = timezone(timedelta(hours=8))
    # Get current time in UTC+8
    now_utc_plus_8 = datetime.now(utc_plus_8)
    # Convert to naive datetime for storage, as per model's sa_column definition
    db_feedback.created_at = now_utc_plus_8.replace(tzinfo=None)

    session.add(db_feedback)
    session.commit()
    session.refresh(db_feedback)
    return db_feedback


def get_feedback_since(
    session: Session, since_datetime_utc: datetime
) -> List[models.UserFeedback]:
    """
    Retrieves all feedback entries created since the given UTC datetime.
    The database stores naive datetimes (assumed to be UTC+8).
    We need to convert the `since_datetime_utc` to naive UTC+8 for comparison.
    """
    utc_plus_8_tz = timezone(timedelta(hours=8))
    since_datetime_local_naive = since_datetime_utc.astimezone(utc_plus_8_tz).replace(
        tzinfo=None
    )

    statement = select(models.UserFeedback).where(
        and_(
            models.UserFeedback.created_at is not None,  # Corrected None check
            models.UserFeedback.created_at >= since_datetime_local_naive,  # type: ignore
        )
    )
    results = session.exec(statement)
    return list(results.all())  # Convert to list


def get_feedback_for_date_range(
    session: Session, start_date: date, end_date: date
) -> List[models.UserFeedback]:
    """
    Retrieves feedback entries within a specific date range (inclusive).
    Timestamps in DB are naive, assumed to be UTC+8.
    """
    start_datetime_naive = datetime.combine(start_date, datetime.min.time())
    end_datetime_naive = datetime.combine(end_date, datetime.max.time())

    statement = select(models.UserFeedback).where(
        and_(
            models.UserFeedback.created_at is not None,  # Corrected None check
            models.UserFeedback.created_at >= start_datetime_naive,  # type: ignore
            models.UserFeedback.created_at <= end_datetime_naive,  # type: ignore
        )
    )
    results = session.exec(statement)
    return list(results.all())  # Convert to list
