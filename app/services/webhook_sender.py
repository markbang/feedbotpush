# app/services/webhook_sender.py
import httpx
from datetime import datetime, timedelta, timezone
from app.core.config import settings


def send_summary_to_webhook(summary: str, summary_type: str) -> bool:
    """
    Sends the summarized feedback to the configured webhook URL.
    Returns True if successful, False otherwise.
    """
    if (
        not settings.WEBHOOK_URL
        or settings.WEBHOOK_URL == "your_webhook_url_please_set_in_env"
    ):
        print(
            "Webhook URL is not configured. Please set WEBHOOK_URL in your .env file."
        )
        return False
    utc_plus_8 = timezone(timedelta(hours=8))
    now_utc_plus_8 = datetime.now(utc_plus_8).strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "text_tag_list": [
                    {
                        "tag": "text_tag",
                        "text": {"tag": "plain_text", "content": str(now_utc_plus_8)},
                        "color": "#DFFAFF",
                    }
                ],
                "title": {"tag": "plain_text", "content": f"{summary_type}"},
                "template": "wathet",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": summary,
                        "tag": "lark_md",
                    },
                }
            ],
        },
    }

    try:
        with httpx.Client() as client:
            response = client.post(settings.WEBHOOK_URL, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        print(f"Summary successfully sent to webhook: {settings.WEBHOOK_URL}")
        return True
    except httpx.RequestError as e:
        print(f"Error sending summary to webhook: {e}")
        return False
    except httpx.HTTPStatusError as e:
        print(
            f"Webhook returned an error: {e.response.status_code} - {e.response.text}"
        )
        return False
