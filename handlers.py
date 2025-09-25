from linebot.v3.messaging import AsyncMessagingApi
from linebot.v3.webhooks import MessageEvent
from supabase import AsyncClient
from openai import AsyncOpenAI
from imgurpython import ImgurClient

# 匯入我們的服務模組
from services import line_service, db_service, ai_service, tarot_service
from services.web_crawler import ptt_crawler
import config

imgur_client = ImgurClient(config.IMGUR_CLIENT_ID, config.IMGUR_CLIENT_SECRET)

async def handle_draw_tarot_card(event, line_bot_api):
    """處理抽塔羅牌指令"""
    image_url = tarot_service.get_random_tarot_image_url(imgur_client)
    await line_service.send_image_message(event, line_bot_api, image_url, image_url)

async def handle_roll_astro_dice(event, line_bot_api):
    """處理占星骰指令"""
    dice_result = tarot_service.roll_astro_dice()
    await line_service.send_text_message(event, line_bot_api, dice_result)

async def handle_hexagram_explanation(event, line_bot_api):
    """處理六芒星說明指令"""
    text_content="牌陣說明: \n              過去\n對方心態          困難點\n              " +\
            "結論\n   未來               現在\n          自己的心態\n全局暗示\n(對方心態)可以換成(環境狀況)"
    await line_service.send_text_message(event, line_bot_api, text_content)

async def handle_show_help_message(event, line_bot_api):
    content="特殊指令:\n\n抽正牌\n骰子卡\n六芒星說明"
    await line_service.send_text_message(event, line_bot_api, content)

async def handle_ptt_beauty(event, line_bot_api):
    """處理 PTT 表特版指令"""
    content = ptt_crawler.ptt_beauty()
    await line_service.send_text_message(event, line_bot_api, content)

async def handle_default_message(
    event: MessageEvent,
    line_bot_api: AsyncMessagingApi,
    db_client: AsyncClient,
    openai_client: AsyncOpenAI
):
    """處理預設訊息（聊天、AI互動）"""
    user_id = event.source.user_id
    message_text = event.message.text
    user_name = None
    try:
        profile = await line_bot_api.get_profile(user_id)
        user_name = profile.display_name
    except Exception as e:
        print(f"用戶未加入吃吃或已封鎖吃吃無法獲取user_name: {e}")
    
    await db_service.upsert_user(db_client, user_id, user_name)
    
    session_id = None
    if event.source.type == 'group':
        group_id = event.source.group_id
        group_name = await line_service.get_group_name(group_id, line_bot_api)
        print("group_name: ", group_name)
        await db_service.save_group_message(db_client, group_id, group_name, user_id, message_text)
        session_id = group_id
    else:
        session_id = await db_service.manage_user_session_and_message(db_client, user_id, message_text)

    if not message_text.endswith('/') and user_id not in config.BLACKLIST_USERS:
        ai_reply = await ai_service.get_ai_response(openai_client, db_client, session_id, user_id, user_name)
        if ai_reply:
            reply_to_save = ai_reply[1] if isinstance(ai_reply, list) and len(ai_reply) > 1 else (ai_reply[0] if isinstance(ai_reply, list) else ai_reply)
            await db_service.save_ai_reply(db_client, session_id, user_id, reply_to_save)
            await line_service.send_text_message(event, line_bot_api, ai_reply)