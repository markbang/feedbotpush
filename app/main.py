from fastapi import FastAPI, Depends
from sqlmodel import Session
import asyncio  # Added asyncio for create_task

from . import (
    crud,
    schemas,
)
from .database import (
    create_db_and_tables,
    get_session,
)
from .tasks.daily_summary import (
    schedule_feedback_summary,
    run_feedback_summary_job,
)
from .core.config import settings  # Moved import to top

create_db_and_tables()


app = FastAPI(
    title="User Feedback API",
    description="API for collecting and managing user feedback.",
    version="0.1.0",
)


@app.post("/feedback/", response_model=schemas.UserFeedbackRead)
def create_feedback_endpoint(
    feedback_in: schemas.UserFeedbackCreate,  # Use the new schema for creation
    session: Session = Depends(get_session),  # Use dependency injection for session
):
    """
    Create new user feedback.
    """
    return crud.create_feedback_db(session=session, feedback_in=feedback_in)


@app.on_event("startup")
async def startup_event():
    # Initialize scheduler or other startup tasks
    print("Application startup: Initializing scheduler...")
    schedule_feedback_summary()  # Call the scheduling function

    # Add a one-time job to run immediately on startup for debugging if configured
    if settings.RUN_SUMMARY_ON_STARTUP:
        print("RUN_SUMMARY_ON_STARTUP is True. Running feedback summary job now...")
        # Running in a separate task to avoid blocking startup
        asyncio.create_task(run_feedback_summary_job())


@app.on_event("shutdown")
async def shutdown_event():
    # Clean up scheduler or other shutdown tasks
    from .tasks.daily_summary import scheduler  # Import scheduler instance

    if scheduler.running:
        print("Application shutdown: Shutting down scheduler...")
        scheduler.shutdown()
