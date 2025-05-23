# app/models.py
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import DateTime
from datetime import datetime


class UserFeedback(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_uid: str
    device_id: int
    app_version: str
    app_channel: str
    user_agent: str
    feedback_type: str
    feedback: str
    image_url: str | None = None
    debug: str | None = None
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False)),  # Storing as naive datetime in DB
    )
