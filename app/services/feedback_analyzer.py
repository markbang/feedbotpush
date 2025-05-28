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
            f"(类型: {fb.feedback_type}, 上传的图片链接: {fb.image_url}) 的反馈:\n{fb.feedback})"
            for fb in feedback_list
        ]
    )

    prompt = f"""请你扮演一位细致的产品分析师助理，帮助我总结以下用户反馈条目。
你的任务是：
1.  识别关键问题、常见抱怨、有价值的建议以及任何积极的反馈。
2.  针对不同`类型`的反馈（如使用问题、功能建议等，根据实际的值）进行归纳。

请提供一个简洁、结构清晰的中文总结报告。
在每个总结点前使用恰当的emoji来增强表达：
    ✅ 表示积极的反馈或已确认的优点。
    ⚠️ 表示需要关注的问题或BUG。
    💡 表示用户的建议或新想法。
    ❓ 表示疑问或不明确的反馈。
    🗣️ 表示普遍提及的抱怨或常见问题。
总结中绝对不能包含用户信息。
请专注于精准描述用户反馈的“内容”，不要添加任何主观评论或改进建议。
如果反馈条目中包含有效的图片链接 (`image_url`不为空或无效链接占位符)，请在总结该条具体反馈时，在其内容后以 "[图片](链接)" 的格式附上。如果链接无效或为空，则忽略。
确保总结内容精炼，突出核心信息。
————————
输出这个格式：
🗣️ 常见抱怨
**双人图难度高**：用户反馈双人图制作极其困难。
**男性角色生成问题**：与描述词不符，被质疑男性角色生成能力。
————————
最终输出只需要总结报告的正文，不要包含任何招呼语或额外的解释性文字。

反馈条目列表如下：
{feedbacks_text}
"""

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位专业的AI产品分析助手，核心任务是根据用户提供的指示，将用户反馈精准地总结为包含emoji、结构清晰的中文报告。请严格遵循用户在后续指示中提出的所有格式和内容要求。- 只能使用加粗, 文字链接, <font color='color'> 颜色文本 </font>这三种markdown格式，绝对不能使用##标题以及`-`无序等其他markdown格式。",
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
