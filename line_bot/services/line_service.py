from linebot.v3.messaging import (
    TextMessage,
    ImageMessage,
    ReplyMessageRequest
)

async def send_text_message(event, line_bot_api, text_content):
    limit = 5000
    if isinstance(text_content, list):
        processed_messages = []
        for text in text_content:
            if len(text) > limit:
                text = text[:limit - 50] + "\n... (因內容過長，已省略部分)"
            processed_messages.append(TextMessage(text=text))
        messages = processed_messages
    else:
        if len(text_content) > limit:
            text_content = text_content[:limit - 50] + "\n... (因內容過長，已省略部分)"
        messages = [TextMessage(text=text_content)]
    await line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=messages
        )
    )

async def send_image_message(event, line_bot_api, oriUrl, preUrl):
    messages = [ImageMessage(original_content_url=oriUrl,
        preview_image_url=preUrl)]
    await line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=messages
        )
    )

async def get_group_name(group_id, line_bot_api):
    try:
        summary = await line_bot_api.get_group_summary(group_id)
        return summary.group_name
    except Exception as e:
        print(f"Error getting group name: {e}")
        return "未知群組"