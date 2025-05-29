# app/services/webhook_sender.py
import httpx
from datetime import datetime, timezone, timedelta
from app.core.config import settings


def send_summary_to_webhook(
    summary: str, summary_type: str, totalnum: int, typestring: str
) -> bool:
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
    utc_plus8 = timezone(timedelta(hours=8))
    now = datetime.now(utc_plus8)
    content = f"""<font color="green">{typestring}</font>\n{summary}
    """
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "text_tag_list": [
                    {
                        "tag": "text_tag",
                        "text": {"tag": "plain_text", "content": f"总反馈{totalnum}条"},
                        "color": "#DFFAFF",
                    },
                    {
                        "tag": "text_tag",
                        "text": {
                            "tag": "plain_text",
                            "content": now.strftime("%Y-%m-%d %H:%M:%S"),
                        },
                        "color": "#59A3B0",
                    },
                ],
                "title": {"tag": "plain_text", "content": summary_type},
                "template": "wathet",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": content,
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
