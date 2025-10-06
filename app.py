import json
import os
import random
import re
import time
import uuid
from datetime import datetime, timezone, timedelta
from urllib import parse
import asyncio
from postgrest.exceptions import APIError

from playwright.async_api import async_playwright
import gspread
import psycopg2
import pyimgur
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, abort
from imgurpython import ImgurClient
from linebot.v3 import WebhookParser
# from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
# from linebot.v3.exceptions import ApiException
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    ImageMessage,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    ShowLoadingAnimationRequest,
    AsyncApiClient,
    AsyncMessagingApi
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from oauth2client.service_account import ServiceAccountCredentials
# from openai import OpenAI
from openai import AsyncOpenAI
# from supabase import Client, create_client
from supabase import AsyncClient, AsyncClientOptions, acreate_client

import config
import handlers

app = Flask(__name__)

configuration = Configuration(access_token=config.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(config.LINE_CHANNEL_SECRET)

@app.route("/")
def hello():
    return "ok!"

@app.route("/callback", methods=['POST'])
async def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    await handle_events(events)
    return 'ok'

async def handle_events(events):
    # 建立一個非同步的 aiohttp session
    async with AsyncApiClient(configuration) as async_api_client,\
            AsyncOpenAI(api_key=config.OPENAI_API_KEY) as openai_client:

        supabase_client = await acreate_client(config.SUPABASE_URL, config.SUPABASE_KEY)

        line_bot_api = AsyncMessagingApi(async_api_client)
        try:
            tasks = []
            for event in events:
                if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                    tasks.append(process_message_event(event, line_bot_api, supabase_client, openai_client))
            
            if tasks:
                await asyncio.gather(*tasks)

        finally:
            await supabase_client.postgrest.aclose()

async def process_message_event(event, line_bot_api, supabase_client, openai_client):
    await line_bot_api.show_loading_animation(#不發送訊息的話如何中斷動畫
        ShowLoadingAnimationRequest(chatId=event.source.user_id, loadingSeconds=60)
    )
    command_parts = event.message.text.split()
    match command_parts:
        # case ["搜尋", keyword]:
        #     await handle_search_ptt(event, keyword)
        # case ["搜尋", *keywords]: # 匹配多個關鍵字
        #     full_keyword = " ".join(keywords)
        #     await handle_search_ptt(event, full_keyword)
        case ["幫助"] | ["help"]:
            await handlers.handle_show_help_message(event, line_bot_api)
        case ["抽正牌"]:
            await handlers.handle_draw_tarot_card(event, line_bot_api)
        case ["骰子卡"]:
            await handlers.handle_roll_astro_dice(event, line_bot_api)
        case ["進階骰子卡"]:
            await handlers.handle_roll_astro_dice_plus(event, line_bot_api)
        case ["六芒星說明"]:
            await handlers.handle_hexagram_explanation(event, line_bot_api)
        case ["表特/"]:
            await handlers.handle_ptt_beauty(event, line_bot_api)
        case ["test"]:
            await handlers.handle_test(event, line_bot_api)
        case _:
            await handlers.handle_default_message(event, line_bot_api, supabase_client, openai_client)
   
if __name__ == '__main__':
    app.run()
