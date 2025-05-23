# app/services/feedback_analyzer.py
import openai
from app.core.config import settings
from ..models import UserFeedback  # Assuming UserFeedback model is in app.models
from typing import List


def summarize_feedback_with_openai(feedback_list: List[UserFeedback]) -> str | None:
    """
    Summarizes a list of user feedback entries using OpenAI.
    """
    if not feedback_list:
        return "No new feedback to summarize."

    if (
        not settings.AI_API_KEY
        or settings.AI_API_KEY == "your_ai_api_key_please_set_in_env"
        or settings.AI_API_KEY == "your_actual_ai_api_key_here"
    ):
        print(
            "OpenAI API key is not configured. Please set AI_API_KEY in your .env file."
        )
        return None  # Or raise an error

    # Configure OpenAI client
    if settings.OPENAI_API_BASE_URL:
        client = openai.OpenAI(
            api_key=settings.AI_API_KEY, base_url=settings.OPENAI_API_BASE_URL
        )
    else:
        client = openai.OpenAI(api_key=settings.AI_API_KEY)  # Pass API key directly

    # Concatenate feedback messages
    # You might want to format this more nicely or handle very long inputs
    feedbacks_text = "\n---\n".join(
        [
            f"(版本: {fb.app_version}, 类型: {fb.feedback_type}, 上传的图片链接: {fb.image_url}) 的反馈:\n{fb.feedback})"
            for fb in feedback_list
        ]
    )

    prompt = f"""请总结以下用户反馈条目。
识别关键问题、常见抱怨和任何积极的反馈。
提供一个简洁的、适合报告的摘要。总结内容请使用中文，并可以适当在语句前添加相关的emoji来增强表达效果，例如使用 ✅ 表示已解决或积极的方面，使用 ⚠️ 表示需要注意的问题，使用 ❓ 表示疑问或不明确的反馈等。
总结中不要包括用户信息，给正文内容就可以，需要精准描述反馈不要给相关改进意见，如有图片请提及并给出markdwon格式超链接就ok，不需要显示。切记是总结
反馈条目:
{feedbacks_text}

摘要:
"""

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个AI助手，负责将用户反馈总结成带有emoji的中文纯文本。",
                },
                {"role": "user", "content": prompt},
            ],
        )
        if (
            response.choices
            and response.choices[0].message
            and response.choices[0].message.content
        ):
            summary_from_openai = response.choices[0].message.content.strip()

            return summary_from_openai
        else:
            print("OpenAI API returned an empty or unexpected response.")
            return None
    except openai.APIStatusError as e:  # More specific error for status-related issues
        print("OpenAI API Status Error encountered:")
        print(f"  Status Code: {e.status_code}")
        print(f"  Message: {e.message}")
        if e.response and hasattr(e.response, "text"):
            print(f"  Response Body: {e.response.text}")
        return None
    except openai.APIError:  # Catch other OpenAI API errors
        print("OpenAI API Error encountered:")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while calling OpenAI API: {e}")
        import traceback

        traceback.print_exc()
        return None
