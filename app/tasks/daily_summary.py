# app/tasks/daily_summary.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta, timezone
from sqlmodel import Session

from app.core.config import settings
from app.database import get_session  # To get a new session for the task
from app.services.feedback_analyzer import summarize_feedback_with_openai
from app.services.webhook_sender import send_summary_to_webhook
from app.crud import get_feedback_since


async def run_feedback_summary_job():
    """
    Job to fetch recent feedback, summarize it, and send it to a webhook.
    """
    print(f"Running feedback summary job at {datetime.now(timezone.utc)}")
    db: Session = next(get_session())  # Get a new database session

    since_datetime_utc = datetime.now(timezone.utc) - timedelta(
        hours=settings.SUMMARY_INTERVAL_HOURS
        if settings.SUMMARY_INTERVAL_HOURS > 0
        else 24
    )

    feedback_to_summarize = get_feedback_since(
        db, since_datetime_utc=since_datetime_utc
    )

    if not feedback_to_summarize:
        print("No new feedback to summarize.")
        db.close()
        return

    print(f"Found {len(feedback_to_summarize)} feedback entries to summarize.")

    summary = summarize_feedback_with_openai(feedback_to_summarize)

    if summary:
        print(
            f"Summary generated: {summary[:200]}..."
        )  # Print first 200 chars of summary
        send_summary_to_webhook(summary)
    else:
        print("Failed to generate summary or summary was empty.")

    db.close()


# Define UTC+8 timezone object
utc_plus_8 = timezone(timedelta(hours=8))

scheduler = AsyncIOScheduler(timezone=utc_plus_8)  # Set scheduler timezone to UTC+8


def schedule_feedback_summary():
    if settings.SUMMARY_INTERVAL_HOURS > 0:
        print(
            f"Scheduling feedback summary to run every {settings.SUMMARY_INTERVAL_HOURS} hours (Timezone: UTC+8)."
        )
        scheduler.add_job(
            run_feedback_summary_job,
            trigger=IntervalTrigger(
                hours=settings.SUMMARY_INTERVAL_HOURS, timezone=utc_plus_8
            ),
            id="feedback_summary_interval",
            name="Feedback Summary (Interval)",
            replace_existing=True,
        )
    elif settings.SUMMARY_SCHEDULE_HOURS:
        hours_str = settings.SUMMARY_SCHEDULE_HOURS
        if isinstance(hours_str, (int, float)):
            hours_str = str(int(hours_str))  # Convert numeric to string if necessary

        if isinstance(hours_str, str):
            hours = [
                int(h.strip()) for h in hours_str.split(",") if h.strip().isdigit()
            ]
            for hour in hours:
                if 0 <= hour <= 23:
                    print(
                        f"Scheduling feedback summary to run daily at {hour:02}:00 (Timezone: UTC+8)."
                    )
                    scheduler.add_job(
                        run_feedback_summary_job,
                        trigger=CronTrigger(hour=hour, minute=0, timezone=utc_plus_8),
                        id=f"feedback_summary_daily_{hour:02}",
                        name=f"Feedback Summary (Daily at {hour:02}:00 UTC+8)",
                        replace_existing=True,
                    )
                else:
                    print(f"Invalid hour ({hour}) in SUMMARY_SCHEDULE_HOURS. Skipping.")
        else:
            print(
                f"SUMMARY_SCHEDULE_HOURS is not a valid string: {hours_str}. Skipping cron scheduling."
            )

    else:
        print(
            "No schedule configured for feedback summary. Set SUMMARY_INTERVAL_HOURS or SUMMARY_SCHEDULE_HOURS."
        )

    if scheduler.get_jobs():
        try:
            if not scheduler.running:
                scheduler.start()
                print("Scheduler started.")
            else:
                print("Scheduler is already running.")
        except Exception as e:
            print(f"Error starting scheduler: {e}")
    else:
        print("No jobs scheduled, scheduler not started.")
