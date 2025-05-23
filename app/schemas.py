# app/schemas.py
from pydantic import BaseModel
from datetime import datetime


class UserFeedbackBase(BaseModel):
    user_uid: str
    device_id: int
    app_version: str
    app_channel: str
    user_agent: str
    feedback_type: str
    feedback: str
    image_url: str | None = None
    debug: str | None = None


class UserFeedbackCreate(UserFeedbackBase):
    pass


class UserFeedbackRead(UserFeedbackBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # For Pydantic v2 (instead of orm_mode in v1)
