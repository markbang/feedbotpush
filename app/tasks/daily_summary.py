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


async def _process_and_send_summary(
    db: Session, since_datetime_utc: datetime, job_name: str
):
    """Helper function to process and send feedback summary."""
    print(
        f"[{job_name}] Fetching feedback since {since_datetime_utc.astimezone(utc_plus_8).strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )
    feedback_to_summarize = get_feedback_since(
        db, since_datetime_utc=since_datetime_utc
    )

    if not feedback_to_summarize:
        print(
            f"[{job_name}] No new feedback to summarize for the period since {since_datetime_utc.astimezone(utc_plus_8).strftime('%Y-%m-%d %H:%M:%S %Z')}."
        )
        return

    print(
        f"[{job_name}] Found {len(feedback_to_summarize)} feedback entries to summarize."
    )
    summary = summarize_feedback_with_openai(feedback_to_summarize)

    if summary:
        print(f"[{job_name}] Summary generated: {summary[:200]}...")
        send_summary_to_webhook(summary, job_name)
    else:
        print(f"[{job_name}] Failed to generate summary or summary was empty.")


async def run_feedback_summary_job():
    """
    Job to fetch recent feedback based on configured interval/schedule, summarize it, and send it to a webhook.
    """
    job_name = "日报"
    print(
        f"Starting {job_name} job at {datetime.now(utc_plus_8).strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )
    db: Session = next(get_session())  # Get a new database session
    try:
        hours_to_look_back = (
            settings.SUMMARY_INTERVAL_HOURS
            if settings.SUMMARY_INTERVAL_HOURS > 0
            else 24
        )
        since_datetime_utc = datetime.now(timezone.utc) - timedelta(
            hours=hours_to_look_back
        )
        await _process_and_send_summary(db, since_datetime_utc, job_name)
    except Exception as e:
        print(f"Error in {job_name}: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print(f"Finished {job_name} job.")
        db.close()


async def run_weekly_feedback_summary_job():
    """
    Job to fetch feedback from the last 7 days, summarize it, and send it to a webhook.
    """
    job_name = "周报"
    print(
        f"Starting {job_name} job at {datetime.now(utc_plus_8).strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )
    db: Session = next(get_session())
    try:
        since_datetime_utc = datetime.now(timezone.utc) - timedelta(days=7)
        await _process_and_send_summary(db, since_datetime_utc, job_name)
    except Exception as e:
        print(f"Error in {job_name}: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print(f"Finished {job_name} job.")
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
            "No daily/interval schedule configured for feedback summary. Set SUMMARY_INTERVAL_HOURS or SUMMARY_SCHEDULE_HOURS."
        )

    # Schedule weekly summary job
    print(
        "Scheduling weekly feedback summary to run on Sunday at 19:00 (Timezone: UTC+8)."
    )
    scheduler.add_job(
        run_weekly_feedback_summary_job,
        trigger=CronTrigger(day_of_week="sun", hour=19, minute=0, timezone=utc_plus_8),
        id="feedback_summary_weekly",
        name="Feedback Summary (Weekly Sun 19:00 UTC+8)",
        replace_existing=True,
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
