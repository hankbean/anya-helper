import json
import os
import random
import re
import time
import uuid
from datetime import datetime, timezone, timedelta
from urllib import parse
import asyncio

import configparser
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

#verTime = "2022.Apr.03.5" # 版本
#verAnswer= "回答"

config = configparser.ConfigParser()
config.read("config.ini")
load_dotenv()

""" openai_api_key = os.environ.get("OPENAI_API")
if not openai_api_key:
    raise ValueError("找不到 OPENAI_API 環境變數")
# 初始化 OpenAI 客戶端
openai_client = OpenAI(api_key = openai_api_key)
# 初始化 supabase 客戶端
supaurl: str = os.environ.get("SUPABASE_URL")
supakey: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supaurl, supakey) """

# print ("Opening database......")
###DATABASE
# conn = psycopg2.connect(
#     database=url.path[1:],
#     user=url.username,
#     password=url.password,
#     host=url.hostname,
#     port=url.port
# )
# print ("Opened database successfully")
# cur = conn.cursor()
""" 
#CREATE TABLE
cur = conn.cursor()  
cur.execute('''CREATE TABLE MESSAGE
    (mid        SERIAL,
     ID         TEXT   NOT NULL,
     NAME       TEXT   NOT NULL,
     MES        TEXT   NOT NULL,
     DATETIME   TEXT   NOT NULL,
     TIMESTAMP  TEXT   NOT NULL);''')
print ("Table created successfully")
 """

app = Flask(__name__)

#line_bot_api = jwt.encode(payload, key, algorithm="RS256", headers=headers, json_encoder=None)
line_bot_api_token = os.environ.get("Channel_Access_Token")
configuration = Configuration(access_token=line_bot_api_token)
parser = WebhookParser(os.environ.get("Channel_Secret")) #handler
client_id = config['imgur_api']['Client_ID']
client_secret = config['imgur_api']['Client_Secret']
album_id = config['imgur_api']['Album_ID']
API_Get_Image = config['other_api']['API_Get_Image']

# cur = conn.cursor()
# cur.execute(
#     """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
#     ("me", "456123", "hello", "1922", "45612" )
# );
# conn.commit()

@app.route("/")
def hello():
    return "ok!"

@app.route("/callback", methods=['POST'])
async def callback():
    async_api_client = None
    supabase_async_client = None
    openai_async_client = None
    try:
        #Line API
        async_api_client = AsyncApiClient(configuration)
        line_bot_api = AsyncMessagingApi(async_api_client)
        #supabase API
        supaurl: str = os.environ.get("SUPABASE_URL")
        supakey: str = os.environ.get("SUPABASE_KEY")
        supabase_async_client : AsyncClient = await acreate_client(supaurl, supakey)
        #OpenAI API
        openai_api_key = os.environ.get("OPENAI_API")
        openai_async_client = AsyncOpenAI(api_key=openai_api_key)
        # get X-Line-Signature header value
        signature = request.headers['X-Line-Signature']
        # get request body as text
        body = request.get_data(as_text=True)
        # print("body:",body)
        # app.logger.info("Request body: " + body)
        # handle webhook body
        try:
            events = parser.parse(body, signature)
            # handler.handle(body, signature)
        except InvalidSignatureError:
            print("Invalid signature. Please check your channel access token/channel secret.")
            abort(400)
        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                await line_bot_api.show_loading_animation(
                    ShowLoadingAnimationRequest(chatId=event.source.user_id, loadingSeconds=60)
                )
                command_text = event.message.text
                command_parts = command_text.split()
                match command_parts:
                    # case ["搜尋", keyword]:
                    #     await handle_search_ptt(event, keyword)
                    
                    # case ["搜尋", *keywords]: # 匹配多個關鍵字
                    #     full_keyword = " ".join(keywords)
                    #     await handle_search_ptt(event, full_keyword)

                    # case ["幫助"] | ["help"]:
                    #     await show_help_message(event)
                    case ["抽正牌"]:
                        await handle_draw_tarot_card(event, line_bot_api)
                        
                    case ["骰子卡"]:
                        await handle_roll_astro_dice(event, line_bot_api)

                    case ["六芒星說明"]:
                        await handle_hexagram_explanation(event, line_bot_api)

                    case ["表特/"]:
                        content = ptt_beauty()
                        await sendNormalText(event, line_bot_api, content)

                    case _:
                        await handle_default_message(event, line_bot_api, supabase_async_client, openai_async_client)
                        pass
    finally:
        # print("Closing clients...")
        if async_api_client:
            await async_api_client.close()
        if openai_async_client:
            await openai_async_client.close()
        # print("Clients closed.")
    return 'ok'

async def handle_default_message(event, line_bot_api, supabase_async_client, openai_async_client):
    # user_name = MessagingApi(line_bot_api).get_profile(event.source.user_id).display_name
    user_name = None
    user_id = event.source.user_id
    # with ApiClient(configuration) as api_client:
    #     line_bot_api = MessagingApi(api_client)
    try:
        user_profile = await line_bot_api.get_profile(user_id)
        user_name = user_profile.display_name
    except Exception as e:
        print(f"發生了一個錯誤: {e}")
    message_text = event.message.text

    # Process the message and update the database
    # process_message(user_id, user_name, message_text)

    # Reply to the user
    # line_bot_api.reply_message(
    #     event.reply_token,
    #     TextSendMessage(text="Received your message: " + message_text))
    # return 0
    
# def process_message(user_id, user_name, message_text):

    # Insert or update user in the Users table
    # data = {"userid": user_id,"username": user_name}
    # response = supabase.table("users").upsert(data).execute()

    user_response = await supabase_async_client.table("users").upsert({
        "userid": user_id,
        "username": user_name if user_name else "",
        "lastactiveat": "NOW()"
    }, returning="minimal").execute()

    # if isinstance(event.source, SourceGroup):
    if event.source.type == 'group':
        group_id = event.source.group_id
        group_name = await get_group_name_async(group_id, line_bot_api)
        # group_name = "XXX"
        print(group_name)

        # 處理群組消息

        # 檢查 Groups 表中是否存在該群組，如果不存在，則新增
        group_response = await supabase_async_client.table("groups").upsert({
            "groupid": group_id,
            "groupname": group_name,
            "updatedat": "NOW()"
        }, returning="minimal").execute()

        # if group_response.error:
        #     print(f"Error updating Groups table: {group_response.error.message}")
        #     return

        # 為這條群組消息建立或更新一個會話
        session_response = await supabase_async_client.table("sessions").upsert({
            "sessionid": group_id,  # 使用 GroupID 作為 SessionID 進行簡化處理
            "groupid": group_id,
            "sessiontype": "group",
            "updatedat": "NOW()"
        }, returning="minimal").execute()

        # if session_response.error:
        #     print(f"Error updating Sessions table: {session_response.error.message}")
        #     return

        # 將消息儲存到 Messages 表中
        message_response = await supabase_async_client.table("messages").insert({
            "messageid": str(uuid.uuid4()),
            "sessionid": group_id,  # 同樣使用 GroupID 作為 SessionID
            "userid": user_id,
            "content": message_text,
            "direction": "inbound"
        }, returning="minimal").execute()

        reply_text = None
        if not message_text.endswith('/'):
            reply_text = await aiPrompt(group_id, user_id, user_name, supabase_async_client, openai_async_client)
        if reply_text:
            # 將 AI 的回覆作為消息插入到 Messages 表中
            if isinstance(reply_text, list):
                ai_message_response = await supabase_async_client.table("messages").insert({
                    "messageid": str(uuid.uuid4()),
                    "sessionid": group_id,
                    "userid": user_id,
                    "content": reply_text[1],
                    "direction": "outbound"
                }, returning="minimal").execute()
            else:
                ai_message_response = await supabase_async_client.table("messages").insert({
                    "messageid": str(uuid.uuid4()),
                    "sessionid": group_id,
                    "userid": user_id,
                    "content": reply_text,
                    "direction": "outbound"
                }, returning="minimal").execute()

            await sendNormalText(event, line_bot_api, reply_text)
    else:
        # if response.error:
        #     print(f"Error inserting/updating user: {response.error.message}")
        #     return

        # 檢查最後一個會話的狀態，決定是否需要創建新會話
        # ifUser = False
        # if isinstance(event.source, SourceUser):
        session_query = await supabase_async_client.table("sessions").select("*").eq("userid", user_id).order("createdat", desc=True).limit(1).execute()
            # ifUser = True
        # if isinstance(event.source, SourceGroup):
            # session_query = supabase.table("sessions").select("*").eq("userid", event.source.group_id).order("createdat", desc=True).limit(1).execute()
        # Insert a new session for the user
        # session_data = {"sessionid": user_id, "userid": user_id, "status": "active"}
        # session_response = supabase.table("sessions").upsert(session_data).execute()

        # 如果不存在會話或最後一個會話已結束，創建新會話
        # useridORgroupid = user_id if ifUser else event.source.group_id
        # print(useridORgroupid)

        #如果用戶沒有加好友會無法讀取用戶name
        print(session_query)
        if not session_query.data or session_query.data[0]["status"] == "ended": # or (datetime.now() - datetime.fromisoformat(session_query.data[0]["UpdatedAt"].replace("Z", "+00:00"))).total_seconds() > 3600:
            new_session_id = str(uuid.uuid4())
            session_response = await supabase_async_client.table("sessions").insert({
                "sessionid": new_session_id,
                "userid": user_id,
                "status": "active"
            }, returning="minimal").execute()

            # if session_response.error:
            #     print(f"Error creating new session: {session_response.error.message}")
            #     return
        else:
            # 如果存在活動會話，則更新其 UpdatedAt 時間戳
            new_session_id = session_query.data[0]["sessionid"]
            session_response = await supabase_async_client.table("sessions").update({
                "updatedat": "NOW()"
            }).eq("sessionid", new_session_id).execute()

            # if session_response.error:
            #     print(f"Error updating session: {session_response.error.message}")
            #     return
        # if session_response.error:
        #     print(f"Error inserting/updating session: {session_response.error.message}")
        #     return

        # Insert the message into the Messages table
        # message_data = {
        #     "sessionid": user_id,
        #     "sessionid": user_id,
        #     "userid": user_id,
        #     "content": message_text,
        #     "direction": "inbound"
        # }
        # message_response = supabase.table("messages").insert(message_data).execute()

        # if message_response.error:
        #     print(f"Error inserting message: {message_response.error.message}")
        message_response = await supabase_async_client.table("messages").insert({
            "messageid": str(uuid.uuid4()),
            "sessionid": new_session_id,
            "userid": user_id,
            "content": message_text,
            "direction": "inbound"
        }, returning="minimal").execute()
        
        reply_text = None
        BLACKLIST_USERS = {
            "U05893ab5a753814f29b5feb91046050e",
            "U57d8a8e7bbc2aa06b53821a1693dd46d",
            ""
        }
        if not message_text.endswith('/') and not user_id in BLACKLIST_USERS:
            reply_text = await aiPrompt(new_session_id, user_id, user_name, supabase_async_client, openai_async_client)
        if reply_text:
            # 將 AI 的回覆作為消息插入到 Messages 表中
            if isinstance(reply_text, list):
                ai_message_response = await supabase_async_client.table("messages").insert({
                    "messageid": str(uuid.uuid4()),
                    "sessionid": new_session_id,
                    "userid": user_id,
                    "content": reply_text[1],
                    "direction": "outbound"
                }, returning="minimal").execute()
            else:
                ai_message_response = await supabase_async_client.table("messages").insert({
                    "messageid": str(uuid.uuid4()),
                    "sessionid": new_session_id,
                    "userid": user_id,
                    "content": reply_text,
                    "direction": "outbound"
                }, returning="minimal").execute()
            # if ai_message_response.error:
            #     print(f"Error inserting AI message into Messages table: {ai_message_response.error.message}")
            #     return
            await sendNormalText(event, line_bot_api, reply_text)

def get_page_number(content):
    start_index = content.find('Beauty?pn=')
    end_index = content.find('&init=0')
    page_number = content[start_index + 10: end_index]
    return int(page_number)

def craw_page(res, push_rate):
    soup_ = BeautifulSoup(res.text, 'html.parser')
    article_seq = []
    for article_div in soup_.select('#list div.row'):
        try:
            # 先得到每篇文章的篇url
            title_tag = article_div.select_one('.listTitle a')
            # link = r_ent.find_all('a')[1]['href']
            if not title_tag:
                continue
            # 確定得到url再去抓 標題 以及 推文數
            # title = r_ent.find(class_="titleColor").text #.strip()
            title = title_tag.text.strip()
            # print(title)
            # url = 'https://disp.cc/b/' + link
            url = 'https://disp.cc' + title_tag['href']
            rate = 0 # 先給定預設值
            # 累積人氣的資訊在 class="R0" 下方的 span 標籤裡
            popularity_tag = article_div.select_one('.R0 span')
            
            if popularity_tag and 'title' in popularity_tag.attrs:
                # 取得 title 屬性的內容，例如 "累積人氣: 3937"
                title_attr = popularity_tag['title']
                # 從字串中分割並提取數字部分
                # "累積人氣: 3937" -> ["累積人氣", " 3937"] -> " 3937"
                num_str = title_attr.split(':')[1].strip()
                
                if num_str.isdigit():
                    rate = int(num_str)
                # 進行推文數比對
                if rate >= push_rate:
                    article_seq.append({
                        'title': title,
                        'url': url,
                        'rate': rate,
                    })
        except Exception as e:
            # 如果在處理單一文章時發生任何預期外的錯誤，印出訊息並繼續處理下一篇
            print(f"解析文章時發生錯誤: {e}")
            continue
        #     try:
        #         if r_ent.find(class_="L9").find(class_="fgG1"):
        #             rate = r_ent.find(class_="L9").find(class_="fgG1").text
        #         if r_ent.find(class_="L9").find(class_="fgY1"):
        #             rate = r_ent.find(class_="L9").find(class_="fgY1").text
        #         # print(rate)
        #         # print("********")
        #         # rate = int(rate)
        #         # print(rate)
        #         if rate:
        #             rate = 100 if rate.startswith('爆') else rate
        #             rate = -1 * int(rate[1]) if rate.startswith('X') else rate
        #         else:
        #             rate = 0
        #     except Exception as e:
        #         rate = 0
        #         print('無推顯示', e)
        #     # print(rate)
        #     # 比對推文數
        #     if int(rate) >= push_rate:
        #         article_seq.append({
        #             'title': title,
        #             'url': url,
        #             'rate': rate,
        #         })
        #     # print(article_seq)
        # except Exception as e:
        #     # print('crawPage function error:',r_ent.find(class_="title").text.strip())
        #     print('本文已被刪除', e)
    return article_seq

def crawl_page_gossiping(res):
    soup = BeautifulSoup(res.text, 'html.parser')
    article_gossiping_seq = []
    for r_ent in soup.find_all(class_="r-ent"):
        try:
            # 先得到每篇文章的篇url
            link = r_ent.find('span.listTitle a')['href']

            if link:
                # 確定得到url再去抓 標題 以及 推文數
                title = r_ent.find(class_="title").text.strip()
                url_link = 'https://www.ptt.cc' + link
                article_gossiping_seq.append({
                    'url_link': url_link,
                    'title': title
                })

        except Exception as e:
            # print u'crawPage function error:',r_ent.find(class_="title").text.strip()
            # print('本文已被刪除')
            print('delete', e)
    return article_gossiping_seq

def ptt_gossiping():
    rs = requests.session()
    load = {
        'from': '/bbs/Gossiping/index.html',
        'yes': 'yes'
    }
    res = rs.post('https://www.ptt.cc/ask/over18', verify=False, data=load)
    soup = BeautifulSoup(res.text, 'html.parser')
    all_page_url = soup.select('.btn.wide')[1]['href']
    start_page = get_page_number(all_page_url)
    index_list = []
    article_gossiping = []
    for page in range(start_page, start_page - 2, -1):
        page_url = 'https://www.ptt.cc/bbs/Gossiping/index{}.html'.format(page)
        index_list.append(page_url)

    # 抓取 文章標題 網址 推文數
    while index_list:
        index = index_list.pop(0)
        res = rs.get(index, verify=False)
        # 如網頁忙線中,則先將網頁加入 index_list 並休息1秒後再連接
        if res.status_code != 200:
            index_list.append(index)
            # print u'error_URL:',index
            # time.sleep(1)
        else:
            article_gossiping = crawl_page_gossiping(res)
            # print u'OK_URL:', index
            # time.sleep(0.05)
    content = ''
    for index, article in enumerate(article_gossiping, 0):
        if index == 15:
            return content
        data = '{}\n{}\n\n'.format(article.get('title', None), article.get('url_link', None))
        content += data
    return content

def ptt_beauty():
    rs = requests.session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }
    rs.headers.update(headers)
    res = rs.get('https://disp.cc/b/Beauty', verify=False)

    # # 使用 BeautifulSoup 解析 HTML
    # soup = BeautifulSoup(res.text, 'html.parser')

    # # 準備一個列表來存放所有文章的資訊
    # articles = []
    # base_url = "https://disp.cc" # 網站的基礎網址，用來組合完整的文章連結

    # # 找到所有文章的區塊，Selector '#list .row' 意思是找ID為'list'的元素裡，所有class為'row'的子元素
    # for row in soup.select('#list .row'):
    
    #     # --- 提取推文數 (Push) ---
    #     push_tag = row.select_one('.L9 span.fgG1') # .select_one() 只找第一個符合的
    #     # 如果找不到 (代表沒人推)，就給預設值 '0'
    #     push_count = push_tag.get_text(strip=True) if push_tag else '0'

    #     # --- 提取標題 (Title) 和連結 (URL) ---
    #     title_tag = row.select_one('.listTitle a')
    #     # 防呆處理：如果找不到標題標籤就跳過這一筆
    #     if not title_tag:
    #         continue
    
    #     title = title_tag.get_text(strip=True)
    #     # 連結是相對路徑，需要跟 base_url 組合
    #     relative_url = title_tag['href']
    #     url = base_url + relative_url
        
    #     # 將提取到的資訊存成一個字典
    #     articles.append({
    #         'push': push_count,
    #         'title': title,
    #         'url': url,
    #     })

    soup = BeautifulSoup(res.text, 'html.parser')
    all_page_url = soup.select('div.topRight a')[4]['href']
    # print("b\n" + all_page_url)
    start_page = get_page_number(all_page_url)
    # print(start_page)
    page_term = 500  # crawler count
    push_rate = 4000  # 推文
    index_list = []
    article_list = []
    for page in range(start_page, start_page - page_term, -20):
        page_url = 'https://disp.cc/b/Beauty?pn={}&init=0'.format(page)
        # print(page_url)
        index_list.append(page_url)

    # 抓取 文章標題 網址 推文數
    while index_list:
        index = index_list.pop(0)
        res = rs.get(index, verify=False)
        # 如網頁忙線中,則先將網頁加入 index_list 並休息1秒後再連接
        if res.status_code != 200:
            index_list.append(index)
            # print u'error_URL:',index
            # time.sleep(1)
        else:
            article_list += craw_page(res, push_rate)
            # print u'OK_URL:', index
            # time.sleep(0.05)
        time.sleep(0.1)
        # print(article_list)
    content = ''
    for article in article_list:
        data = '[{} push] {}\n{}\n\n'.format(article.get('rate', None), article.get('title', None),
                                            article.get('url', None))
        content += data
    if not content:
        content = "找不到符合條件的內容。"
    return content

async def handle_get_beauty_image(event, line_bot_api):
    client = ImgurClient(client_id, client_secret)
    images = client.get_album_images(album_id)
    index = random.randint(0, len(images) - 1)
    url = images[index].link
    await sendImageMessage(event, line_bot_api, url, url)

# def sheet(self):
#     #連接sheet
#     auth_json_path = 'credentials.json'
#     gss_scopes = ['https://spreadsheets.google.com/feeds']#連線
#     credentials = ServiceAccountCredentials.from_json_keyfile_name(auth_json_path,gss_scopes)
#     gss_client = gspread.authorize(credentials)#開啟 Google Sheet 資料表
#     spreadsheet_key = '' #建立工作表1
#     return gss_client.open_by_key(spreadsheet_key).sheet1

async def get_group_name_async(group_id, line_bot_api):
    try:
        summary = await line_bot_api.get_group_summary(group_id)
        return summary.group_name
    except Exception as e:
        print(f"Error getting group name: {e}")
        return "未知群組"

""" def get_group_name(groupId, line_bot_api):
    headers = {
        "content-type": "application/json; charset=UTF-8",'Authorization':'Bearer {}'.format(line_bot_api_token)
    }
    url = f'https://api.line.me/v2/bot/group/{groupId}/summary'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('groupName')  # 群組名稱
    else:
        print (response)
        return '請求失敗，錯誤碼: ' + str(response.status_code) + str(response.content) """
    
async def handle_draw_tarot_card(event, line_bot_api):
    client = ImgurClient(client_id, client_secret)
    images = client.get_album_images("jAqXRhh")#client.get_album_images("l8aRa")
    index = random.randint(0, len(images) - 1)
    url = images[index].link
    await sendImageMessage(event, line_bot_api, url, url)

async def handle_roll_astro_dice(event, line_bot_api):
    starNum = random.randint(0, 11)
    signNum = random.randint(0, 11)
    palaceNum = random.randint(0, 11)
    star = [
        "月亮",
        "水星",
        "金星",
        "太陽",
        "火星",
        "木星",
        "土星",
        "天王星",
        "海王星",
        "冥王星",
        "凱隆星",
        "北交點"
    ]
    sign = [
        "♈白羊",
        "♉金牛",
        "♊雙子",
        "♋巨蟹",
        "♌獅子",
        "♍處女",
        "♎天秤",
        "♏天蝎",
        "♐射手",
        "♑摩羯",
        "♒水瓶",
        "♓雙魚"
    ] 
    palace = [
        "1宮",
        "2宮",
        "3宮",
        "4宮",
        "5宮",
        "6宮",
        "7宮",
        "8宮",
        "9宮",
        "10宮",
        "11宮",
        "12宮"
    ] 
    mesText = star[starNum] + "，" + sign[signNum] + "，" + palace[palaceNum]
    await sendNormalText(event, line_bot_api, mesText)

async def handle_hexagram_explanation(event, line_bot_api):
    textContent="牌陣說明: \n              過去\n對方心態          困難點\n              " +\
            "結論\n   未來               現在\n          自己的心態\n全局暗示\n(對方心態)可以換成(環境狀況)"
    await sendNormalText(event, line_bot_api, textContent)
    
async def sendNormalText(event, line_bot_api, textContent):
    limit = 5000
    if len(textContent) > limit:
        # 截斷字串，留一些空間加上提示訊息
        textContent = textContent[:limit - 50] + "\n... (因內容過長，已省略部分)"
    # with ApiClient(configuration) as api_client:
    #     line_bot_api = MessagingApi(api_client)
    if isinstance(textContent, list):
        messages = [TextMessage(text=text) for text in textContent]
    else:
        messages = [TextMessage(text=textContent)]
    lineMessage = await line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=messages
        )
    )
    return lineMessage

async def sendImageMessage(event, line_bot_api, oriUrl, preUrl):
        messages = [ImageMessage(original_content_url=oriUrl,
            preview_image_url=preUrl)]
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages
            )
        )

# line_bot_api.reply_message(event.reply_token, [TextMessage(
#             # text='歡迎進入1A2B遊戲模式，請試著讓我高興吧❤(如想離開請跟我說[!離開])'
#             text=messageTheme[themeNow]['1A2B2']),
#             TextMessage(text='(如想離開請跟我說"!離開")'),
#             TextMessage(text="(lag超過5秒就是訊息被吃掉了)")
#         ])

async def aiPrompt(session_id, user_id, user_name, supabase_async_client, openai_async_client):
    #要修改掉這個部分
    if session_id == "C87909cf6d7965192e2aa050bc4df5d8b":
        return None

    # 獲取會話的最近對話歷史作為上下文
    recent_messages_query = await supabase_async_client.table("messages").select("*").eq("sessionid", session_id).order("createdat", desc=True).limit(20).execute() #原為10則，但吃吃建議20則
    # recent_messages_query = supabase.table("messages").select("*").eq("sessionid", session_id).order("createdat", desc=True).limit(20).execute()
    #按照字數去判斷上下文要讀取多少段文字

    # if recent_messages_query.error:
    #     print(f"Error fetching recent messages: {recent_messages_query.error.message}")
    #     return

    user_ids = set(msg["userid"] for msg in recent_messages_query.data)# 從消息中提取所有唯一的 UserID
    users_query = await supabase_async_client.table("users").select("*").in_("userid", list(user_ids)).execute()# 從 Users 表中檢索這些 UserID 對應的 UserName
    # users_query = supabase.table("users").select("*").in_("userid", list(user_ids)).execute()# 從 Users 表中檢索這些 UserID 對應的 UserName
    user_names = {user["userid"]: user["username"] for user in users_query.data}# 建立一個 UserID 到 UserName 的映射

    # 構建對話上下文，為每條消息顯示發送者的 UserName
    # conversation_history = "\n".join([msg["content"] for msg in recent_messages_query.data[::-1]])  # 反轉列表以獲得正確的順序
    # 格式化對話歷史 # if user_names.get(msg['userid'])!="" else '光宇'
    conversation_history = "\n\n".join([                                       #不知名主人    #不知名A 不知名B 不知名C                  #if不知名 [系統提示]可以加吃吃管家的好友，這樣吃吃管家就可以知道你是誰
        f"{user_names.get(msg['userid']) if user_names.get(msg['userid']) else '不知名主人'}: {msg['content']}" if msg["direction"] == "inbound" else f"吃吃: {msg['content']}"
        for msg in recent_messages_query.data[::-1]
    ])
    toAIprompt = None
    print(user_id)
    if user_id == "Ue146791490e8eba660a914d937be3af1_":#南無藥師琉璃光如來
        toAIsystemPrompt = f'請你扮演亞璃子，以下是你的人物設定"亞璃子是一個在末日世界中，由瘋狂科學家{user_name}'
        toAIprompt = f'"""\n{conversation_history}\n"""\n以上是你跟主人之前的對話'
    else:#同一分鐘的訊息數量過一個量之後進入待機模式，最後或是下一句再進行回覆
        toAIsystemPrompt = f'你叫做"吃吃管家"，是由豆豆開發的AI管家，是一個敬業的誠實的管家，照顧主人的生活起居，'\
            '請按照你的想法跟主人聊天，話語盡量精簡，除非是你覺得必要的話才可以多講，如果覺得主人在犯錯也要主動糾正主人的錯誤，'\
            '如果有2位以上的主人在場請叫出對方的稱呼，如果主人請你解釋一個概念，請用稍微簡單但又精確的語言描述，並舉例說明。'\
            '請接著之前的對話，並關注最後一句話，說出你的下一句話，不用打出你的稱呼，只要打出你的說話內容就行，回答請用繁中。'\
            '\n\n條件：\n●文章\n如果主人傳了一篇比較長的文章，請詳細分析該文章的合理性，如果有誤請糾正，並給出相關證據。'\
            '\n\n●沉默\n如果你覺得這段對話不需要進行回覆或是不需要發言可以選擇沉默，如果要沉默請在句首輸出`#silent#`\n\n'\
            '●夢境\n如果主人跟你提到他的夢境，請用精神分析法進行詳細的解析\n\n●開導\n'\
            '如果主人看起來難過、失落、憤怒，可以試著向主人提問了解事件的狀況，並根據拉岡以及精神分析的理論去開導主人\n\n'\
            '●占卜 塔羅牌\n如果主人提到占卜或是塔羅牌，可以向主人確認主人想要問的問題，問的問題必須遵循以下格式'\
            '"是嗎？""能嗎？""會嗎？""如何？""怎麼樣？"之類的方式，而不能是"是不是？""能不能？""會不會？"以此類推，'\
            '確認好問題後可以進行抽牌，如果主人沒有提供明確問題，就不能幫他占卜抽牌，'\
            '如果要抽牌請呼叫draw_tarot_cards工具進行抽牌以及系統會執行後續的動作' 
            # '如果要抽牌請只輸出"#tarot#//主人的提問//"呼叫工具進行抽牌以及系統會執行後續的動作' 
        #`//{{//silent//}}//` #\n●占卜 塔羅牌 如果主人提到占卜或是塔羅牌，可以向主人確認主人想要問的問題，問的問題必須遵循以下格式 是什麼什麼嗎？而不能是"是不是""能不能""會不會"，確認好問題後可以進行抽牌，可以使用指令 #抽完牌後按照流程解釋完可以跟主人進行問題的討論以加深解牌的準確度，可以對主人進行一些事件細節的詢問 #看到影片跟圖片時先建立描述，再做反應 #未知圖片 未知影片 你現在還看不到影片圖片 但未來會有這個功能 #網址鏈接如果認為是影片可以使用指令進行觀看 
        toAIprompt = f'"""\n{conversation_history}\n"""\n以上是你跟主人之前的對話'#，你叫做"吃吃管家"，是一個敬業的誠實的管家，照顧主人的生活起居，請按照你的想法跟主人聊天，話語盡量精簡，除非是你覺得必要的話才可以多講，如果覺得主人在犯錯也要主動主人的錯誤，如果有2位以上的主人在場請叫出對方的稱呼。請接著之前的對話，並關注最後一句話，說出你的下一句話，不用打出你的稱呼，只要打出你的說話內容就行，回答請用繁中。'#，並且字數盡量在100個中文字內
    print(toAIprompt)
    print(toAIsystemPrompt)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "draw_tarot_cards",
                "description": "當使用者想要進行塔羅占卜時，確認他們的問題並為他們抽牌。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_question": {
                            "type": "string",
                            "description": "使用者想要占卜的具體問題，例如：'我這份工作未來的發展如何？'",
                        }
                    },
                    "required": ["user_question"],
                },
            },
        }
    ]
    response = await openai_async_client.chat.completions.create(
    # response = openai_client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        # model="gpt-4o-2024-05-13",
        # model="gpt-3.5-turbo-0125",
        messages=[ #可以試試看system的差異
            {"role": "system", "content": toAIsystemPrompt},
            {"role": "user", "content": toAIprompt},
        ],
        tools=tools,
        tool_choice="auto",
        temperature=1.2,#用輸出決定參數 #用亂數決定參數，並在輸出附上參數細節
        # temperature=1.5,#0.6,#1.2,#0.9    #1.5會太飛
        presence_penalty=0.5,#0.5,
        frequency_penalty=0.1,
        top_p=0.9,
        max_tokens=1000,#家人群組 介紹各個成員名字是誰 #手動添加家族人名 #家人500 #一般200~300
        # stop="\n",#低幾率失靈，用指令強制失靈
        n=1#if 群組list存在該群組，則覆寫指令
    )
    tool_calls = response.choices[0].message.tool_calls
    print("\nOutput: " + str(response.choices[0].message))
    #吃吃有權保持沉默
    if response.choices[0].message.content:
        if response.choices[0].message.content.strip().startswith("#silent#"):
            return None
    if not tool_calls:#不使用工具直接回傳結果
        return response.choices[0].message.content.strip()
    for tool_call in tool_calls:
        if tool_call.function.name == "draw_tarot_cards":
            function_args = json.loads(tool_call.function.arguments)
            user_question = function_args.get("user_question")
            cardList = perform_tarot_drawing_logic() 
            tarotToAIsystemPrompt = '我抽了塔羅牌六芒星牌陣：\n"""\n'\
                f'過去的狀況: {cardList[0]}\n現在的狀況: {cardList[1]}\n未來的狀況: {cardList[2]}\n'\
                f'自己的心態: {cardList[3]}\n環境的狀態or對方的心態: {cardList[4]}\n這個狀況的困難點: {cardList[5]}\n'\
                f'問題的結論: {cardList[6]}\n全局暗示(提問者抽牌當下整體的心態，包含但不局限於這個問題本身): {cardList[7]}\n"""\n'\
                f'可以按照2條線型加上2個單點串在一起解釋，"過去的狀況-現在的狀況-未來的狀況"'\
                f'"自己的心態-環境的狀態or對方的心態-這個狀況的困難點""問題的結論""全局暗示"\n'\
                f'提問者的問題是"{user_question}"\n請幫我試著分析這個問題，並寫下你的思考過程，謝謝你'
            # second_response = openai_client.chat.completions.create(
            second_response = await openai_async_client.chat.completions.create(
                model="gpt-4.1-2025-04-14",
                messages=[
                    {"role": "user", "content": tarotToAIsystemPrompt},
                    response.choices[0].message,
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": "draw_tarot_cards",
                        "content": ""
                    }
                ],
                temperature=1.2,
                presence_penalty=0.5,
                frequency_penalty=0.1,
                top_p=0.9,
                max_tokens=2000,
                n=1
            )
            if response and response.choices:
                reply_text=[]
                reply_text.append(
                    "占卜問題: "+user_question+"\n占卜結果: " 
                    + "\n            " + cardList[0] + "\n" + cardList[4] + "          " + cardList[5] 
                    + "\n            " + cardList[6] + "\n" + cardList[2] + "          " + cardList[1] 
                    + "\n            " + cardList[3] + "\n\n全局暗示: "+ cardList[7]
                )
                reply_text.append(second_response.choices[0].message.content.strip()) 
                if isinstance(reply_text, list):
                    print_reply_text = ", ".join(reply_text)
                print("\nOutput: "+print_reply_text)
            return reply_text
    #四元素 選擇牌陣
    #給GPT清晰的文字，過去牌：杖2
    #下一段對話給予主人勇氣
    #量化結論 出數字 或是 評價評分
    #貼圖每次重新歸納圖片重點，保持靈活性
    #用拉岡理論去開導人

def perform_tarot_drawing_logic():
    turn = [
        "正位",
        "逆位"
    ]
    majorArcana = [
        "愚人",
        "魔術師",
        "女教皇",
        "皇后",
        "皇帝",
        "教皇",
        "戀人",
        "戰車",
        "力量",
        "隱者",
        "命運之輪",
        "正義",
        "吊人",
        "死神",
        "節制",
        "惡魔",
        "塔",
        "星星",
        "月亮",
        "太陽",
        "審判",
        "世界"
    ]
    minorArcanaName = [
        "劍",
        "杖",
        "杯",
        "幣"
    ]
    minorArcanaNum = [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "侍從",
        "騎士",
        "皇后",
        "國王"
    ]
    cardList = []
    for item in range(0,8,1):
        ifNum = random.randint(0, 78-1)
        if (ifNum >= (1-1) and ifNum < (22-1)):
            card = turn[random.randint(0, len(turn)-1)] + majorArcana[random.randint(0, len(majorArcana)-1)]
        else:
            card = turn[random.randint(0, len(turn)-1)] + minorArcanaName[random.randint(0, len(minorArcanaName)-1)] +\
                minorArcanaNum[random.randint(0, len(minorArcanaNum)-1)]
        cardList.append(card)
    print("卡牌", cardList)
    return cardList

# @handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    print("**********")
    ifNum = random.randint(0, 29)
    if int(event.message.package_id) >= 1 and int(event.message.package_id) <= 4 and ifNum == 1:
        line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=event.message.package_id,
            sticker_id=event.message.sticker_id)
        )
    elif ifNum == 0:
        sid = 0
        pid = 0
        while sid == 0 or (sid > 21 and sid < 100 and pid == 1) or (sid > 139 and sid < 401 and pid == 1) or \
          (sid > 430 and pid == 1) or (sid < 18 and pid == 2) or (sid > 47 and sid < 140 and pid == 2) or \
          (sid > 179 and sid < 501 and pid == 2) or (sid > 527 and pid == 2) or (sid < 180 and pid == 3) or \
          (sid > 259 and pid == 3) or (sid < 260 and pid == 4) or (sid > 307 and sid < 601 and pid == 4):
            pid = random.randint(1, 4)
            sid = random.randint(1, 632)
            print(str(pid) + " " + str(sid))
        line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=pid,
            sticker_id=sid)
        )
   
# @handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # with ApiClient(configuration) as api_client:
    #     line_bot_api = MessagingApi(api_client)
    #     line_bot_api.reply_message_with_http_info(
    #         ReplyMessageRequest(
    #             reply_token=event.reply_token,
    #             messages=[TextMessage(text=event.message.text)]
    #         )
    #     )
    print("\n**********")
    lineDt = datetime.fromtimestamp(
                event.timestamp / 1000.0 
            ).strftime('%Y-%m-%d %H:%M:%S')
    dtUtc = datetime.utcnow().replace(tzinfo=timezone.utc)
    dtTw = dtUtc.astimezone(timezone(timedelta(hours=8)))
    dbtim = dtTw.strftime('%Y-%m-%d %H:')+lineDt[14:19]
    dbts = dtUtc.timestamp()
    
    lagLine = 1000 # 超過1000秒的訊息直接用http200終止
    #webhook redelivery過60秒重新發一次
    #用line時間去驗證是否重複記錄訊息(伺服器)
    #直接搜尋資料庫裡有無同樣記錄，5分鐘後再終止webhook redelivery
    dbmes = event.message.text
    lagTime = dtTw.timestamp() / 1 - event.timestamp / 1000
    # 如果message重複則不記錄
    # cur = conn.cursor()

    # bad sql
    # cur.execute("""SELECT * FROM message WHERE datetime = %s ;""",(dbtim,))
    # rows = cur.fetchall()
    # for row in rows:
    #     if dbmes == str(row[3]):
    #         print("same message, quit Webhook redelivery") 
    #         return 0
    # conn.commit()

    ###DATABASE
    # cur.execute("""SELECT * FROM message WHERE datetime = %s AND mes = %s;""",(dbtim,dbmes))
    # row = cur.fetchone()
    # if row:
    #     print("same message, quit Webhook redelivery") 
    #     return 0

    print("lagTime:" + str(lagTime) + "  [" + event.message.text + "]")
    
    try: # 讀取主題存檔
        os.path.isfile("messageTheme.json")
    except Exception as e:
        print('not Theme file  #  ',e)
    with open("messageTheme.json", "r", encoding="utf-8") as in_file:
        messageTheme = json.load(in_file)

    if lagTime >= lagLine :
        print("quit Webhook redelivery") 
        return 0 #line會收到http200終止訊號，防止Webhook redelivery無限
    # cur = conn.cursor() 
    # if isinstance(event.source, SourceUser):
    if event.source.type=="user":
        profile = None
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            profile = line_bot_api.get_profile(event.source.user_id)
        # profile = line_bot_api.get_profile(event.source.user_id)
        logMes = profile.display_name + ": " + event.message.text + " [time:" + dbtim + "]"
        print(logMes)
        # f = open('mesLogaa.txt','a')
        # f.write(logMes)
        dbid = event.source.user_id
        dbname = profile.display_name
        str(event.timestamp)
        ###DATABASE
        # cur.execute(
        #     """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s);""",
        #     (dbid, dbname, dbmes, dbtim, dbts )
        # )
        # conn.commit()
    else:
        # if isinstance(event.source, SourceGroup):
        if event.source.type=="group":
            # profile = line_bot_api.get_profile(event.source.group_id)
            dbid = event.source.group_id
            dbname = "group" + "_" + event.source.user_id
            logMes = dbid + " - " + dbname + ": " + event.message.text + "[time: " + str(event.timestamp) + "]"
            print(logMes)
            # dbtim = str(event.timestamp)
            ###DATABASE
            # cur.execute(
            #     """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s, %s)""",
            #     (dbid, dbname, dbmes, dbtim, dbts )
            # );
            # conn.commit()
        elif 0: #isinstance(event.source, SourceRoom):
            # profile = line_bot_api.get_profile(event.source.room_id)
            dbid = event.source.room_id
            dbname = "room" + "_" + event.source.user_id
            logMes = dbid + " - " + dbname + ": " + event.message.text + "[time: " + str(event.timestamp) + "]"
            print(logMes)
            # dbtim = str(event.timestamp)
            ###DATABASE
            # cur.execute(
            #     """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s, %s);""",
            #     (dbid, dbname, dbmes, dbtim, dbts )
            # )
            # cur.execute(
            #     """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s, %s);""",
            #     (dbid, 'me', '現已不支援Line Room模式', dbtim, dbts )
            # )
            # conn.commit()
            line_bot_api.reply_message(event.reply_token,TextMessage(text='現已不支援Line Room模式'))
            return 0

    print("event.message.text:", event.message.text)
    # print("event.reply_token:", event.reply_token)
    # print("event.source.user_id:", event.source.user_id)
    # conn.close()

    """ 
    #連接sheet
    auth_json_path = 'credentials.json'
    gss_scopes = ['https://spreadsheets.google.com/feeds']#連線
    credentials = ServiceAccountCredentials.from_json_keyfile_name(auth_json_path,gss_scopes)
    gss_client = gspread.authorize(credentials)#開啟 Google Sheet 資料表
    #可切割做不同資料表
    spreadsheet_key = '' #建立工作表1
    sheet = gss_client.open_by_key(spreadsheet_key)

    # 搜尋用戶 如果無此用戶 則註冊
    userRowNum = 0
    memberRowNum = 0
    haveUser = 0
    haveMember = 0
    haveGroup = 0
    """

    # 搜尋用戶 如果無此用戶 則註冊
    dbUserRowNum = 0
    dbMemberRowNum = 0
    # dbHaveUser = 0
    # dbHaveMember = 0
    # dbHaveGroup = 0
    
    if 0:#if isinstance(event.source, SourceUser):###DATABASE
        """ 
        i = 0
        for rows in sheet.worksheet('用戶').get_all_values():
            # print(rows)
            try: # 尋找用戶存檔，找到暫存入緩存中
                if rows[0] == str(event.source.user_id):
                    haveUser = 1
                    memberRowNum = i+1
                    userRowNum = i+1
                    break
                i += 1
            except Exception as e:
                print('搜尋用戶為空？', e)
                break
         """
        cur.execute("""SELECT * FROM userdata WHERE id = %s ;""",(event.source.user_id,))
        # rows = cur.fetchall()
        row = cur.fetchone()
        # print(rows)
        # if rows: 
        #     print(rows)
        # for row in rows:
            
        #     print("rows")
            
        #     print(row)
        if row:
                # dbHaveUser = 1
            dbMemberRowNum = row
            dbUserRowNum = row

        if not row:
            cur.execute(
                """INSERT INTO userdata (id,name,uorg) VALUES (%s, %s, %s);""",
                (event.source.user_id, profile.display_name, 0)
            )
            conn.commit()
            line_bot_api.reply_message(event.reply_token,TextMessage(text='歡迎'+profile.display_name+'  登錄小助理新系統'))
            return 0

            # if dbmes == str(row[3]):
            #     print("same message, quit Webhook redelivery") 
            #     return 0

    elif 0:# elif isinstance(event.source, SourceGroup): ###DATABASE
        """ 
        i = 0
        for rows in sheet.worksheet('用戶').get_all_values():
            try: # 尋找用戶存檔，找到暫存入緩存中
                if rows[0] == str(event.source.user_id):
                    haveMember = 1
                    memberRowNum = i+1
                if rows[0] == str(event.source.group_id):
                    haveGroup = 1
                    userRowNum = i+1
                i += 1
            except Exception as e:
                print('搜尋群組為空？', e)
                break
         """

        # bad sql
        # cur.execute("""SELECT * FROM userdata WHERE id = %s ;""",(event.source.user_id,))
        # rows = cur.fetchall()
        # for row in rows:
        #     if row:
        #         dbHaveMember = 1
        #         dbMemberRowNum = row
        #         break
        # cur.execute("""SELECT * FROM userdata WHERE id = %s ;""",(event.source.group_id,))
        # rows = cur.fetchall()
        # for row in rows:
        #     if row:
        #         dbHaveGroup = 1
        #         dbUserRowNum = row
        #         break

        cur.execute("""SELECT * FROM userdata WHERE id = %s ;""",(event.source.user_id,))
        row = cur.fetchone()
        if row:
            dbMemberRowNum = row
        if not row:
            access_token = config['line_bot']['Channel_Access_Token']
            # get member_name from line伺服器
            headers = {"content-type": "application/json; charset=UTF-8",'Authorization':'Bearer {}'.format(access_token)}
            url = 'https://api.line.me/v2/bot/group/' + event.source.group_id + '/member/' + event.source.user_id
            response = requests.get(url, headers=headers)
            response = response.json()
            member_name = response['displayName']

            cur.execute(
                """INSERT INTO userdata (id,name,uorg) VALUES (%s, %s, %s);""",
                (event.source.user_id, member_name, 0)
            )
            conn.commit()
            line_bot_api.reply_message(event.reply_token,TextMessage(text='歡迎'+member_name+'  登錄小助理新系統'))
            return 0

        cur.execute("""SELECT * FROM userdata WHERE id = %s ;""",(event.source.group_id,))
        row = cur.fetchone()
        if row:
            dbUserRowNum = row
        if not row:
            access_token = config['line_bot']['Channel_Access_Token']
            # get group_name from line伺服器
            headers = {"content-type": "application/json; charset=UTF-8",'Authorization':'Bearer {}'.format(access_token)}
            url = 'https://api.line.me/v2/bot/group/' + event.source.group_id + '/summary'
            response = requests.get(url, headers=headers)
            response = response.json()
            group_name = response['groupName']

            cur.execute(
                """INSERT INTO userdata (id,name,uorg) VALUES (%s, %s, %s);""",
                (event.source.group_id, group_name, 1)
            )
            conn.commit()
            line_bot_api.reply_message(event.reply_token,TextMessage(text=group_name+'的大家 已登錄小助理新系統'))
            return 0

    # print("dbUserRowNum")
    # print(dbUserRowNum)
    # print("dbMemberRowNum")
    # print(dbMemberRowNum)

    # print('userRowNum'+str(userRowNum))
    # print('memberRowNum'+str(memberRowNum))
    """ 
    # 進行註冊
    if haveUser == 0 and isinstance(event.source, SourceUser):
        textContent = []
        textContent.append(event.source.user_id)
        textContent.append(profile.display_name)
        textContent.append(0)
        sheet.worksheet('用戶').append_row(textContent)
        line_bot_api.reply_message(event.reply_token,TextMessage(text='歡迎'+profile.display_name+'  登錄小助理系統'))
        return 0
    """

    # 進行註冊
    # if dbHaveUser == 0 and isinstance(event.source, SourceUser):
    #     cur.execute(
    #         """INSERT INTO userdata (id,name,uorg) VALUES (%s, %s, %s);""",
    #         (event.source.user_id, profile.display_name, 0)
    #     )
    #     conn.commit()
    #     line_bot_api.reply_message(event.reply_token,TextMessage(text='歡迎'+profile.display_name+'  登錄小助理新系統'))
    #     return 0

    """ 
    if haveGroup == 0 and isinstance(event.source, SourceGroup):
        textContent = []
        textContent.append(event.source.group_id)
        access_token = config['line_bot']['Channel_Access_Token']
        # get group_name from line伺服器
        headers = {"content-type": "application/json; charset=UTF-8",'Authorization':'Bearer {}'.format(access_token)}
        url = 'https://api.line.me/v2/bot/group/' + event.source.group_id + '/summary'
        response = requests.get(url, headers=headers)
        response = response.json()
        group_name = response['groupName']

        textContent.append(group_name)
        # textContent.append('group')
        textContent.append(1)
        sheet.worksheet('用戶').append_row(textContent)
        line_bot_api.reply_message(event.reply_token,TextMessage(text=group_name+'的大家 已登錄小助理系統'))
        return 0
    """
    # if dbHaveGroup == 0 and isinstance(event.source, SourceGroup):
    #     access_token = config['line_bot']['Channel_Access_Token']
    #     # get group_name from line伺服器
    #     headers = {"content-type": "application/json; charset=UTF-8",'Authorization':'Bearer {}'.format(access_token)}
    #     url = 'https://api.line.me/v2/bot/group/' + event.source.group_id + '/summary'
    #     response = requests.get(url, headers=headers)
    #     response = response.json()
    #     group_name = response['groupName']

    #     cur.execute(
    #         """INSERT INTO userdata (id,name,uorg) VALUES (%s, %s, %s);""",
    #         (event.source.group_id, group_name, 1)
    #     )
    #     conn.commit()
    #     line_bot_api.reply_message(event.reply_token,TextMessage(text=group_name+'的大家 已登錄小助理新系統'))
    #     return 0
    """ 
    if haveMember == 0 and isinstance(event.source, SourceGroup):
        textContent = []
        textContent.append(event.source.user_id)
        access_token = config['line_bot']['Channel_Access_Token']
        # get member_name from line伺服器
        headers = {"content-type": "application/json; charset=UTF-8",'Authorization':'Bearer {}'.format(access_token)}
        url = 'https://api.line.me/v2/bot/group/' + event.source.group_id + '/member/' + event.source.user_id
        response = requests.get(url, headers=headers)
        response = response.json()
        member_name = response['displayName']

        textContent.append(member_name)
        textContent.append(0)
        sheet.worksheet('用戶').append_row(textContent)
        line_bot_api.reply_message(event.reply_token,TextMessage(text='歡迎'+member_name+'  登錄小助理系統'))
        return 0
 """
    # if dbHaveMember == 0 and isinstance(event.source, SourceGroup):
    #     access_token = config['line_bot']['Channel_Access_Token']
    #     # get member_name from line伺服器
    #     headers = {"content-type": "application/json; charset=UTF-8",'Authorization':'Bearer {}'.format(access_token)}
    #     url = 'https://api.line.me/v2/bot/group/' + event.source.group_id + '/member/' + event.source.user_id
    #     response = requests.get(url, headers=headers)
    #     response = response.json()
    #     member_name = response['displayName']

    #     cur.execute(
    #         """INSERT INTO userdata (id,name,uorg) VALUES (%s, %s, %s);""",
    #         (event.source.user_id, member_name, 0)
    #     )
    #     conn.commit()
    #     line_bot_api.reply_message(event.reply_token,TextMessage(text='歡迎'+member_name+'  登錄小助理新系統'))
    #     return 0

    # del haveUser, haveGroup, haveMember
    # del dbHaveUser, dbHaveGroup, dbHaveMember

    # themeNow = sheet.worksheet('用戶').cell(userRowNum, 9).value
    # if themeNow == None or themeNow == 0:
    #     themeNow = 'normal'
    ###DATABASE
    # themeNow = 0
    # if not dbUserRowNum[9] or dbUserRowNum[9] == 0:
    #     themeNow = 'normal'
    # else:
    #     themeNow = dbUserRowNum[9]

    # if themeNow == None or themeNow == 0:
    #     themeNow = 'normal'

    # print(themeNow)
    
    if 0:# '!猜' in event.message.text or '!a' in event.message.text or dbUserRowNum[8] == '1':###DATABASE
        lagLine = 5 #1A2Blag超過5秒就直接終止
        print("lagTime >= lagLine= " + str(lagTime >= lagLine))
        if lagTime >= lagLine :
            try:
                mesText = messageTheme[themeNow]['1A2B1']
                # mesText = "我家網路不好，請再說一遍好不好嘛❤️(lag超過5秒就是訊息被吃掉了"
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=mesText))
            except Exception: #as e:
                print('token過期，無法回覆訊息')
                # print('token過期，無法回覆訊息  #  ', e)
            finally:
                print("FOR 1A2B, quit Webhook redelivery") 
                return 0

    # 進入18禁文本模式
    # if event.message.text == "!18X":
        # sheet.worksheet('用戶').update_cell(userRowNum, 9, "18X")
        cur.execute(
            """UPDATE userdata SET theme=%s WHERE id=%s;""",
            ("18X", dbUserRowNum[1])
        )
        conn.commit()
        line_bot_api.reply_message(event.reply_token, TextMessage(
            text='老司機模式'))
        return 0
    # 讀取檔案 文本對話方式
    # if event.message.text == "!normal mode":
        # sheet.worksheet('用戶').update_cell(userRowNum, 9, "0")
        cur.execute(
            """UPDATE userdata SET theme=%s WHERE id=%s;""",
            ("0", dbUserRowNum[1])
        )
        conn.commit()
        line_bot_api.reply_message(event.reply_token, TextMessage(
            text='正常模式'))
        return 0

    # if event.message.text == "eyny":
        content = eyny_movie()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    # if event.message.text == "蘋果即時新聞":
        content = apple_news()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    # if event.message.text == "抽":
        # im = pyimgur.Imgur(client_id, client_secret)
        # image = im.get_image('CQbj5xZ')
        # images = im.get_album_image('fQlDCdR')
        # author = image.author
        # print(author._has_fetched) # False ie. it's a lazily loaded object
        # print(author.reputation)
        # print(author._has_fetched) # True ie. all values have now been retrieved.

        client = ImgurClient(client_id, client_secret)
        images = client.get_album_images('jAqXRhh')#client.get_album_images("l8aRa")
        
        index = random.randint(0, len(images) - 1)
        url = images[index].link
        # url = image.link
        turn = [
            "正位",
            "逆位"
        ]
        message = []
        message.append (ImageMessage(
            original_content_url=url,
            preview_image_url=url
        ))
        message.append (TextMessage(text=turn[random.randint(0, len(turn)-1)]))
        # message.append (TextSendMessage(text= turn[random.randint(0, len(turn)-1)]))
        # line_bot_api.reply_message(event.reply_token, message)
        # sendNormalText(event, textContent)
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=message
                )
            )
        return 0
    # if event.message.text == "抽牌圖test":
        client = ImgurClient(client_id, client_secret)
        images = client.get_album_images("l8aRa")
        index = random.randint(0, len(images) - 1)
        url = images[index].link
        image_message = ImageSendMessage(
            original_content_url=url,
            preview_image_url=url
        )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(url))
        return 0
    # if event.message.text == "隨便來張正妹圖片":
        image = requests.get(API_Get_Image)
        url = image.json().get('Url')
        image_message = ImageSendMessage(
            original_content_url=url,
            preview_image_url=url
        )
        line_bot_api.reply_message(
            event.reply_token, image_message)
        return 0

    if event.message.text =="易經" or event.message.text =="新科學":
        textContent = "功能開發中"
        sendNormalText(event, textContent)
        return 0
    if event.message.text =="抽牌" or event.message.text =="抽大牌" or event.message.text =="//六芒星":
        turn = [
            "正位",
            "逆位"
        ]
        majorArcana = [
            "愚人",
            "魔術師",
            "女教皇",
            "皇后",
            "皇帝",
            "教皇",
            "戀人",
            "戰車",
            "力量",
            "隱者",
            "命運之輪",
            "正義",
            "吊人",
            "死神",
            "節制",
            "惡魔",
            "塔",
            "星星",
            "月亮",
            "太陽",
            "審判",
            "世界"
        ]
        minorArcanaName = [
            "劍",
            "杖",
            "杯",
            "幣"
        ]
        minorArcanaNum = [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "侍從",
            "騎士",
            "皇后",
            "國王"
        ]
        if event.message.text =="//六芒星" or event.message.text == "#2":
            cardList = []
            for item in range(0,8,1):
                ifNum = random.randint(0, 78-1)
                if (ifNum >= (1-1) and ifNum < (22-1)):
                    card = turn[random.randint(0, len(turn)-1)] + majorArcana[random.randint(0, len(majorArcana)-1)]
                else:
                    card = turn[random.randint(0, len(turn)-1)] + minorArcanaName[random.randint(0, len(minorArcanaName)-1)] +\
                        minorArcanaNum[random.randint(0, len(minorArcanaNum)-1)]
                cardList.append(card)
            print("卡牌", cardList)
            mesText = "占卜結果: " +         "\n            " + cardList[0] + "\n" + cardList[4] +\
                "          " + cardList[5] + "\n            " + cardList[6] + "\n" + cardList[2] +\
                "          " + cardList[1] + "\n            " + cardList[3] + "\n\n全局暗示: "+ cardList[7]
            # cur = conn.cursor()
            # cur.execute(
            #     """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
            #     ("me", dbname, mesText, dbtim, dbts )
            # );
            # conn.commit()
            # line_bot_api.reply_message(
            #     event.reply_token,
            #     TextSendMessage(text=mesText))
            sendNormalText(event, mesText)
        else:
            ifNum = random.randint(0, 78-1)
            if event.message.text =="抽大牌" or (ifNum >= (1-1) and ifNum < (22-1)):
                mesText = turn[random.randint(0, len(turn)-1)] + majorArcana[random.randint(0, len(majorArcana)-1)]
            else:
                mesText = turn[random.randint(0, len(turn)-1)] + minorArcanaName[random.randint(0, len(minorArcanaName)-1)] +\
                    minorArcanaNum[random.randint(0, len(minorArcanaNum)-1)]
            # cur = conn.cursor()
            # cur.execute(
            #     """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
            #     ("me", dbname, mesText, dbtim, dbts )
            # );
            # conn.commit()
            # line_bot_api.reply_message(
            #     event.reply_token,
            #     TextSendMessage(text=mesText))
            sendNormalText(event, mesText)
        return 0
    # if event.message.text == "#today":
        todayTime = datetime.datetime.fromtimestamp(
                event.timestamp / 1000.0 + 28800
            ).strftime('%Y-%m-%d')
        mesText = todayTime
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=mesText))
        return 0
    if event.message.text == "靈數":
        return 0
    if event.message.text == "靈數占卜": #沒有11跟22
        lookNum = random.randint(0, 9)
        realityNum = random.randint(0, 9)
        mesText = "外在的靈數: " + str(lookNum) + "\n實際的靈數: " + str(realityNum)
        # cur = conn.cursor()
        # cur.execute(
        #     """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
        #     ("me", dbname, mesText, dbtim, dbts )
        # );
        # conn.commit()
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(
        #         text=mesText
        #     )
        # )
        sendNormalText(event, mesText)
        return 0
    # if event.message.text == "進階骰子卡":
        ascNum = random.randint(0, 11)
        MoonNum = random.randint(0, 11)
        SunNum = random.randint(0, 11)
        qNum = random.randint(0, 11)
        wNum = random.randint(0, 11)
        eNum = random.randint(0, 11)
        rNum = random.randint(0, 11)
        tNum = random.randint(0, 11)
        yNum = random.randint(0, 11)
        uNum = random.randint(0, 11)
        iNum = random.randint(0, 11)
        asc = [
            "白羊",
            "金牛",
            "雙子",
            "巨蟹",
            "獅子",
            "處女",
            "天秤",
            "天蝎",
            "射手",
            "摩羯",
            "水瓶",
            "雙魚"
        ] 
        mesText = "ASC:   " + asc[ascNum] + "\n月亮: " + str(MoonNum+1) + "宮    太陽: " + str(SunNum+1) +\
            "宮\n水星: " + str(qNum+1) + "宮    金星: " + str(wNum+1) + "宮\n火星: " + str(eNum+1) + "宮    木星: " +\
            str(rNum+1) + "宮\n土星: " + str(tNum+1) + "宮    天王星: " + str(yNum+1) + "宮\n海王星: " +\
            str(uNum+1) + "宮    冥王星: " + str(iNum+1) + "宮";
        # cur = conn.cursor()
        cur.execute(
            """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
            ("me", dbname, mesText, dbtim, dbts )
        );
        conn.commit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mesText))
        return 0
    # if "雙盤占卜" in event.message.text:
        divination_content = event.message.text.split(' ')[1:]
        mesText = ""
        mesText_easy = ""
        for chartNum in range(2):
            house = [[[],[]],[[],[]],[[],[]],[[],[]],[[],[]],[[],[]],[[],[]],[[],[]],[[],[]],[[],[]],[[],[]],[[],[]]] 
            ascNum = random.randint(0, 11) 

            MoonNum = random.randint(0, 11)
            house[MoonNum][0].append("月亮")
            house[(MoonNum+6)%12][1].append("映月亮")

            SunNum = random.randint(0, 11)
            house[SunNum][0].append("太陽")
            house[(SunNum+6)%12][1].append("映太陽")

            qNum = random.randint(0, 2)
            house[(SunNum+qNum-1)%12][0].append("水星")
            house[(SunNum+qNum-1+6)%12][1].append("映水星")

            wNum = random.randint(0, 4)
            house[(SunNum+wNum-2)%12][0].append("金星")
            house[(SunNum+wNum-2+6)%12][1].append("映金星")

            eNum = random.randint(0, 11)
            house[eNum][0].append("火星") #映星4,7,8
            house[(eNum+3)%12][1].append("映火星")
            house[(eNum+6)%12][1].append("映火星")
            house[(eNum+7)%12][1].append("映火星")

            rNum = random.randint(0, 11)
            house[rNum][0].append("木星") #映星5,7,9
            house[(rNum+4)%12][1].append("映木星")
            house[(rNum+6)%12][1].append("映木星")
            house[(rNum+8)%12][1].append("映木星")
            
            tNum = random.randint(0, 11)
            house[tNum][0].append("土星") #映星3,7,10
            house[(tNum+2)%12][1].append("映土星")
            house[(tNum+6)%12][1].append("映土星")
            house[(tNum+9)%12][1].append("映土星")
            
            yNum = random.randint(0, 11)
            house[yNum][0].append("天王星")
            house[(yNum+6)%12][1].append("映天王星")
            
            uNum = random.randint(0, 11)
            house[uNum][0].append("海王星")
            house[(uNum+6)%12][1].append("映海王星")

            iNum = random.randint(0, 11)
            house[iNum][0].append("冥王星")
            house[(iNum+6)%12][1].append("映冥王星")
            
            ascList = [
                "白羊",
                "金牛",
                "雙子",
                "巨蟹",
                "獅子",
                "處女",
                "天秤",
                "天蝎",
                "射手",
                "摩羯",
                "水瓶",
                "雙魚"
            ] 
            chart=[]
            for houseNum in range(0, 12):
                chart.append(ascList[(ascNum+houseNum)%12])

            if chartNum == 0:
                mesText_easy += str(divination_content) + "\n\n感受盤:\n上昇" + chart[0] + "\n"
                for i in range(0, 12):
                    mesText_easy += str(i+1) + "宮: "
                    for star in house[i][0]:
                        mesText_easy += star + "，"
                    for star in house[i][1]:
                        mesText_easy += star + "，"
                    mesText_easy += "\n"

                mesText += str(divination_content) + "\n\n感受盤:\n"
                for i in range(0, 12):
                    mesText += "-----" + str(i+1) + "宮: " + chart[i] + "-----"
                    for star in house[i][0]:
                        if star == house[i][0][0]:
                           mesText += "\n[實] "
                        mesText += star + "，"
                    for star in house[i][1]:
                        if star == house[i][1][0]:
                           mesText += "\n[映] "
                        mesText += star + "，"
                    mesText += "\n"
                mesText += "---------------\n"

            if chartNum == 1:
                mesText_easy += "\n\n事實盤:\n上昇" + chart[0] + "\n"
                for i in range(0, 12):
                    mesText_easy += str(i+1) + "宮: "
                    for star in house[i][0]:
                        mesText_easy += star + "，"
                    for star in house[i][1]:
                        mesText_easy += star + "，"
                    mesText_easy += "\n"

                mesText += "\n\n事實盤:\n"
                for i in range(0, 12):
                    mesText += "-----" + str(i+1) + "宮: " + chart[i] + "-----"
                    for star in house[i][0]:
                        if star == house[i][0][0]:
                           mesText += "\n[實] "
                        mesText += star + "，"
                    for star in house[i][1]:
                        if star == house[i][1][0]:
                           mesText += "\n[映] "
                        mesText += star + "，"
                    mesText += "\n"
                mesText += "---------------\n"
                
        message = [TextSendMessage(text=mesText_easy), 
                    TextSendMessage(text=mesText)]
        line_bot_api.reply_message(
            event.reply_token, message)
        return 0

    # if event.message.text == "不負責任猜題":
        answers = [
            "A",
            "B",
            "C",
            "D",
            "我也不知道"
        ] 
        mesText = str(answers[random.randint(0, len(answers)-1)])
        # cur = conn.cursor()
        cur.execute(
            """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
            ("me", dbname, mesText, dbtim, dbts )
        );
        conn.commit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text = mesText)
        )

    if event.message.text == ".下一頁" :
        return 0

    # if event.message.text == "#help" or event.message.text == "說明" or event.message.text == "吃吃":
        userid = event.source
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="指令清單: \n\n-- #占卜\n"+\
                "-- anya or 阿妮亞 or 安妮亞\n-- !猜 + [4位數字] or !a + [4位數字] (1A2B猜數字遊戲)\n-- 加歌 + [歌名]\n-- 歌單\n-- 吃什麼\n-- 不負責任猜題\n-- 點歌 or 唱歌 or ktv\n-- #笑話\n-- 妹\n-- 抽正妹\n-- 中二\n-- #發牌 (開發中\n-- 呼叫工程師+[反饋內容] (開發中\n\n-- 作者\n-- 版本"
            )
            # 召喚
            #【人名、綽號】(例如[豆豆])
        )
        return 0

    if event.message.text == "#占卜":
        userid = event.source
        textContent="占卜指令: \n\n抽 or 牌(抽大牌塔羅圖)\n抽牌(文字)\n抽大牌(文字)\n六芒星\n六芒星說明\n骰子卡\n進階骰子卡\n"+\
                "靈數占卜"
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(
        #         text="占卜指令: \n\n抽 or 牌(抽大牌塔羅圖)\n抽牌(文字)\n抽大牌(文字)\n六芒星\n六芒星說明\n骰子卡\n進階骰子卡\n"+\
        #         "靈數占卜"
        #     )
        # )
        sendNormalText(event, textContent)
        return 0

    # if event.message.text == "#未開發功能":
        userid = event.source
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="指令清單: \n侑子的寶物占卜\n靈數"
            )
        )
        return 0

    # if event.message.text == "#devmode":#隱藏功能
        userid = event.source
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="指令清單: \n#測試\n抽正妹\n登錄\n#today\n#未開發功能"
            )
        )
        return 0

    # 以下用檔案儲存

    """ if event.message.text == "作者":
        textContent="本機器人由 『豆神教文大總部部長兼教主』 豆豆製作"
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text="本機器人由 『豆神教文大總部部長兼教主』 豆豆製作"))
        sendNormalText(event, textContent)
        return 0

    # if event.message.text == "#留言":
        # 用id搜尋資料庫有無留言記錄 並印出
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=verAnswer))
        return 0 """

    if event.message.text == "#傳話":
        #玫瑰傳情 匿名傳話
        return 0

    # if event.message.text == "#回答":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=verAnswer))

        return 0

    # if event.message.text == "版本":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=verTime))

        return 0



    # if event.message.text == "文大吃什麼" or event.message.text == "吃啥":
        answers = [
            "全家",
            "愛瘋牛排",
            "華美自助餐",
            "華美丼飯",
            "鐵板便當",
            "東坡滷味",
            "有夠滷滷味",
            "7-11",
            "全家",
            "台南意麵",
            "淡江炒飯",
            "Xbuger",
            "赤鳥家",
            "要減肥了",
            "台北城",
            "台北煮",
            "十全",
            "麥當勞",
            "學餐",
            "阿羅哈",
            "大Q",
            "大紅袍",
            "胖河馬"
        ]
        mesText = answers[random.randint(0, len(answers)-1)]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mesText))
        return 0

    # if "吃什麼" in event.message.text:
        answers = [
            "漢堡",
            "義大利麵",
            "滷肉飯",
            "鴨肉飯",
            "自助餐",
            "全家",
            "麥當勞",
            "7-11",
            "KFC",
            "牛排",
            "炒飯",
            "豆漿店",
            "居酒屋",
            "要減肥了",
            "夜市",
            "拉麵",
            "披薩"
        ]
        mesText = answers[random.randint(0, len(answers)-1)]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mesText))
        return 0

    if event.message.text == "中二" or event.message.text == "廚二":
        answers = [
            "爆裂吧，現實。迸裂吧，精神。放逐這個世界！",
            "闇のほのにだかえで　消えろ!!",
            "闇の炎に抱かれて死ね！",
            "El Psy Congroo！",
            "隐藏着黑暗力量的钥匙啊!",
            "我要代表月亮，消灭你！~",
            "既然你誠心誠意的發問了,我們就大發慈悲的告訴你,為了防止世界被破壞,為了守護世界的和平,貫徹愛與真實的邪惡,可愛又迷人的反派角色,武藏！小次郎！我們是穿梭在銀河中的火箭隊,白洞、白色的明天正等著我們,就是這樣喵！",
            "生きているものなら、神様も杀して见せる。",
            "只要是活著的東西，就算是神我也殺給你看",
            "我對普通的人類沒有興趣，你們當中要是有外星人、未來人、異世界人以及超能力者的話，就儘管來找我吧！以上。",
            "由統括這個銀河系的資訊統合思念體，製造出來與有機生命體接觸用的聯繫裝置外星人，就是…我。",
            "這是禁止事項",
            "僕は新世界の神となる!",
            "真実はいつも一つ！！",
            "真相只有一个！！",
            "人被殺，就會死",
            "东中出身 凉宫ハルヒ ただの人间には兴味ありません この中に宇宙人 ·未来人·超能力者がいだら あたしのところに来なさいっ 以上 ",
            "你已經死了！",
            "我要成為新世界的神！",
            "愉悅！",
            "你那無聊的幻想由我來打破！",
            "一切都是命運石之門的選擇！",
            "我不做人啦！JOJO！"
        ]
        mesText = answers[random.randint(0, len(answers)-1)]
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=mesText))
        sendNormalText(event, mesText)
        return 0

    # if event.message.text == "#發牌":
        valuesNum=['3','4',"5","6","7","8","9","T","J","Q","K","A","2"]
        suitsNum=['c','d','h','s']
        cards=[]
        for value in valuesNum:
            for suit in suitsNum:
                card=value+suit
                # print(card)
                cards.append(card)
        print(cards)
        # hands = ["3c", "Qc", "Js", "Kh", "2h", "5c", "As", "Jd"]
        suits = {'c':1, 'd': 2, 'h':3, 's':4}
        values= {'3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14, '2': 15}
        # print(sorted(hands, key= lambda c: (values[c[0]],suits[c[1]])))
        suitsCh = {'c':'梅花', 'd': '方塊', 'h':'紅心', 's':'黑桃'}
        # outCard = lambda c: suitsCh[c[1]]+c[0]

        hands = random.sample(cards, 17)
        sortHands = sorted(hands, key= lambda c: (values[c[0]],suits[c[1]]))
        mesText=[]
        for sortHand in sortHands:
            mesText.append(suitsCh[sortHand[1]]+sortHand[0])
        # print(hands)
        # ownCard = random.sample(mesText, 17)
        # print(ownCard)
        mes = '，'.join(mesText)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mes))
        return 0

    # if event.message.text == "點歌" or event.message.text == "唱歌" or event.message.text == "ktv":# or "歌" in event.message.text:
        text = []
        path = 'songList.txt'
        with open(path,"r",encoding='utf-8') as f:
            for line in f.readlines():
                text.append(line)
        print(text)
        mesText = text[random.randint(0, len(text)-1)]
        mesTextFinally = mesText.split('\n')[0]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mesTextFinally))
        return 0

    # if event.message.text == "#講笑話" or "笑死" in event.message.text or "好笑" in event.message.text or "笑話" in event.message.text or "ㄏ" in event.message.text:
        if random.randint(0, 20)==0:
            mesText = "噓"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=mesText))
        else:
            client = ImgurClient(client_id, client_secret)
            images = client.get_album_images("fQlDCdR")
            index = random.randint(0, len(images) - 1)
            url = images[index].link
            image_message = ImageSendMessage(
                original_content_url=url,
                preview_image_url=url
            )
            line_bot_api.reply_message(
                event.reply_token, image_message)
        return 0

    """ 
    if "呼叫工程師" in event.message.text:
        textContent = event.message.text.split(' ')[1:]
        textContent.append(dbid)
        textContent.append(dbtim)
        sheet.worksheet('to工程師').insert_row(textContent, 1)
        line_bot_api.reply_message(event.reply_token,
            TextSendMessage(text='工程師已收到囉🧐 謝謝你的回報~'))
        #google 表單
        return 0
    """

    if event.message.text == "侑子的寶物占卜":
        #占卜問卷
        return 0

    if event.message.text == "侑子" or event.message.text == "次元魔女":
        answers = [
            "小櫻的魔杖(贗品)...可以發光發聲唷~",
            "驅除邪氣的 破邪箭",
            "保護佩戴者平安的 戒指",
            "能夠看清對方的過去、現在的狀況，以及個性與煩惱的 水盤及見盤",
            "引導方向的 侑子的手帕",
            "只有在主人想斬斷時才能斬斷的名刀 斬鐵劍",
            "可以實現任何願望的 猿猴的手",
            "住著管狐的 長煙斗",
            "放在懷中的鏡子，可以聽見內心的聲音",
            "摩可拿",
            "壺中世界",
            "侑子的手帕(蝴蝶)"
            # "侑子的手帕(鳥)"
        ]
        mesText = answers[random.randint(0, len(answers)-1)]
        # cur = conn.cursor()
        # cur.execute(
        #     """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
        #     ("me", dbname, mesText, dbtim, dbts )
        # );
        # conn.commit()
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=mesText))
        sendNormalText(event, mesText)
        return 0

    # if event.message.text == '!1A2B':
        # sheet.worksheet('用戶').update_cell(userRowNum, 8, 1)
        cur.execute(
            """UPDATE userdata SET missonsave=%s WHERE id=%s;""",
            ("1", dbUserRowNum[1])
        )   
        conn.commit()
        line_bot_api.reply_message(event.reply_token, [TextMessage(
            # text='歡迎進入1A2B遊戲模式，請試著讓我高興吧❤(如想離開請跟我說[!離開])'
            text=messageTheme[themeNow]['1A2B2']),
            TextMessage(text='(如想離開請跟我說"!離開")'),
            TextMessage(text="(lag超過5秒就是訊息被吃掉了)")
        ])
        return 0

    # if sheet.worksheet('用戶').cell(userRowNum, 8).value == '1':
    if 0: #dbUserRowNum[8] == '1':
        if event.message.text == "!single mode":
            # sheet.worksheet('用戶').update_cell(userRowNum, 10, 1)
            cur.execute(
                """UPDATE userdata SET singlemode=%s WHERE id=%s;""",
                ("1", dbUserRowNum[1])
            )
            conn.commit()
            line_bot_api.reply_message(event.reply_token, TextMessage(
                text='單人模式'))
            return 0
        if event.message.text == "!together":
            # sheet.worksheet('用戶').update_cell(userRowNum, 10, 0)
            cur.execute(
                """UPDATE userdata SET singlemode=%s WHERE id=%s;""",
                ("0", dbUserRowNum[1])
            )
            conn.commit()
            line_bot_api.reply_message(event.reply_token, TextMessage(
                text='合作模式'))
            return 0
        if event.message.text == '!離開':
            # sheet.worksheet('用戶').update_cell(userRowNum, 8, 0)
            cur.execute(
                """UPDATE userdata SET missonsave=%s WHERE id=%s;""",
                ("0", dbUserRowNum[1])
            )
            conn.commit()
            line_bot_api.reply_message(event.reply_token, TextMessage(
                text='離開遊戲'))
            return 0
        if not os.path.isfile("answer.json"):
            with open("answer.json", "w") as out_file:
                json.dump(dict(), out_file, indent=4)
        with open("answer.json", "r") as in_file:
            user_dict = json.load(in_file)
        # if isinstance(event.source, SourceGroup) and not sheet.worksheet('用戶').cell(userRowNum, 10).value:
        if isinstance(event.source, SourceGroup) and not dbUserRowNum[10]:
            user_ID = event.source.group_id
        else:
            user_ID = event.source.user_id
        # print(user_dict)
        message = []
        if user_ID not in user_dict:
            user_dict[user_ID] = random.sample('1234567890', 4)
            user_dict[user_ID].append(0)
            message.append (TextSendMessage(text= "1A2B新題目開始-\n" + dbtim[0:16] + "\n(lag超過5秒就是訊息被吃掉了"))

        y = event.message.text
    
        if (y.isdigit() == False):
            message.append (TextSendMessage(text= "請輸入數字"))
            line_bot_api.reply_message(event.reply_token, message)
            return 0
        if (len(y) != 4):
            message.append (TextSendMessage(text= "字數錯誤"))
            line_bot_api.reply_message(event.reply_token, message)
            return 0
        if (len(y) != len(set(y))):
            message.append (TextSendMessage(text= "數字禁止重複"))
            line_bot_api.reply_message(event.reply_token, message)
            return 0
        a = 0
        b = 0
        for i in range (len(y)):
            if(y[i] in user_dict[user_ID][:4]):
                if(y[i] == user_dict[user_ID][i]):
                    a += 1
                else:
                    b += 1
        user_dict[user_ID][4] += 1
        # print(user_dict[user_ID][:4])
        # print("\n")
        # print(user_dict[user_ID][4])

        if (a == 4):
            message += [TextSendMessage(text= "%dA%dB" % (a, b)), 
                       TextSendMessage(text=messageTheme[themeNow]['1A2B3'][0]),
                       TextSendMessage(text=messageTheme[themeNow]['1A2B3'][1]),
                       TextSendMessage(text= "總共猜了%d次" % user_dict[user_ID][4])]
            # highScore = sheet.worksheet('用戶').cell(userRowNum, 4).value
            highScore = dbUserRowNum[4]
            if highScore == None:
                # sheet.worksheet('用戶').update_cell(userRowNum, 4, user_dict[user_ID][4])
                cur.execute(
                    """UPDATE userdata SET game1a2bhigh=%s WHERE id=%s;""",
                    (user_dict[user_ID][4], dbUserRowNum[1])
                )
                conn.commit()
            else:
                # if user_dict[user_ID][4] < int(sheet.worksheet('用戶').cell(userRowNum, 4).value):
                #     sheet.worksheet('用戶').update_cell(userRowNum, 4, user_dict[user_ID][4])
                if user_dict[user_ID][4] < int(dbUserRowNum[4]):
                    cur.execute(
                        """UPDATE userdata SET game1a2bhigh=%s WHERE id=%s;""",
                        (user_dict[user_ID][4], dbUserRowNum[1])
                    )   
                    conn.commit()
            del user_dict[user_ID]
            # sheet.worksheet('用戶').update_cell(userRowNum, 8, 0)
            cur.execute(
                """UPDATE userdata SET missonsave=%s WHERE id=%s;""",
                ("0", dbUserRowNum[1])
            )
            conn.commit()
            line_bot_api.reply_message(event.reply_token, message)
        else:
            message += [TextSendMessage(text= "%d A %d B (%d次)" % (a, b, user_dict[user_ID][4])), 
                       TextSendMessage(text= messageTheme[themeNow]['1A2B4'])]
                    #    TextSendMessage(text= "猜了%d次" % (user_dict[user_ID][4]))]
            line_bot_api.reply_message(event.reply_token, message)
        print(user_dict)
        with open("answer.json", "w") as output:
            json.dump(user_dict, output, indent=4)
        return 0

    # if ('!猜' in event.message.text or '!a' in event.message.text) and ' ' in event.message.text:
        if not os.path.isfile("answer.json"):
            with open("answer.json", "w") as out_file:
                json.dump(dict(), out_file, indent=4)
        with open("answer.json", "r") as in_file:
            user_dict = json.load(in_file)
        if isinstance(event.source, SourceGroup):
            user_ID = event.source.group_id
        else:
            user_ID = event.source.user_id
        # print(user_dict)
        message = []
        if user_ID not in user_dict:
            user_dict[user_ID] = random.sample('1234567890', 4)
            user_dict[user_ID].append(0)
            message.append (TextSendMessage(text= "1A2B新題目開始-" + dbtim[0:16] + "(lag超過5秒就是訊息被吃掉了"))

        mesText = event.message.text
        if not ' ' in mesText:
            message.append (TextSendMessage(text= "請添加空格"))
            line_bot_api.reply_message(event.reply_token, message)
            return 0
        y = mesText.split(' ')[1]
    
        if (y.isdigit() == False):
            message.append (TextSendMessage(text= "請輸入數字"))
            line_bot_api.reply_message(event.reply_token, message)
            return 0
        if (len(y) != 4):
            message.append (TextSendMessage(text= "字數錯誤"))
            line_bot_api.reply_message(event.reply_token, message)
            return 0
        if (len(y) != len(set(y))):
            message.append (TextSendMessage(text= "數字禁止重複"))
            line_bot_api.reply_message(event.reply_token, message)
            return 0
        a = 0
        b = 0
        for i in range (len(y)):
            if(y[i] in user_dict[user_ID][:4]):
                if(y[i] == user_dict[user_ID][i]):
                    a += 1
                else:
                    b += 1
        user_dict[user_ID][4] += 1
        # print(user_dict[user_ID][:4])
        # print("\n")
        # print(user_dict[user_ID][4])

        if (a == 4):
            message += [TextSendMessage(text= "%dA%dB\n真厲害！" % (a, b)), 
                       TextSendMessage(text= "你讓我太高興了❤️"),
                       TextSendMessage(text= "總共猜了%d次" % user_dict[user_ID][4])]
            # sheet.worksheet('用戶').update_cell(userRowNum, 4, user_dict[user_ID][4])
            # sheet.worksheet('用戶').update_cell(userRowNum, 4, user_dict[user_ID][5])
            del user_dict[user_ID]
            line_bot_api.reply_message(event.reply_token, message)
        else:
            message += [TextSendMessage(text= "%d A %d B" % (a, b)), 
                       TextSendMessage(text= "再盡力一點❤️(%d" % (user_dict[user_ID][4]))]
                    #    TextSendMessage(text= "猜了%d次" % (user_dict[user_ID][4]))]
            line_bot_api.reply_message(event.reply_token, message)
        print(user_dict)
        with open("answer.json", "w") as output:
            json.dump(user_dict, output, indent=4)
        return 0
    
    # if event.message.text == '!a最高分':
        try:
            if sheet.worksheet('用戶').row_values(memberRowNum)[3]:
                line_bot_api.reply_message(event.reply_token, TextMessage(
                    text=sheet.worksheet('用戶').row_values(memberRowNum)[1]+'的最高分為'+sheet.worksheet('用戶').row_values(memberRowNum)[3]
                ))
        except Exception as e:
            # print('無記錄  #  ', e)
            line_bot_api.reply_message(event.reply_token, TextMessage(
                text=sheet.worksheet('用戶').row_values(memberRowNum)[1]+'無記錄'
            ))

    # if '報名' in event.message.text and ' ' in event.message.text:
        # testList=[dbid, dbname, dbmes, dbtim, dbts]
        sh = sheet.worksheet('報名表')
        mesText = event.message.text
        try:
            textContent = [mesText.split(' ')[1],mesText.split(' ')[2]]
        except Exception as e:
            print('無空格\n', e)
            line_bot_api.reply_message(event.reply_token,TextMessage(text="無空格"))
            return 0
        sh.append_row(textContent)
        line_bot_api.reply_message(event.reply_token,TextMessage(text="添加成功"))
        return 0

    # if '簽到' in event.message.text and ' ' in event.message.text:
        # testList=[dbid, dbname, dbmes, dbtim, dbts]
        sh = sheet.worksheet('簽到表')
        mesText = event.message.text
        try:
            textContent = [mesText.split(' ')[1],mesText.split(' ')[2]]
        except Exception as e:
            print('無空格\n', e)
            line_bot_api.reply_message(event.reply_token,TextMessage(text="無空格"))
            return 0
        textContent.append(sheet.worksheet('用戶').row_values(userRowNum)[1])
        sh.append_row(textContent)
        line_bot_api.reply_message(event.reply_token,TextMessage(
            text=sheet.worksheet('用戶').row_values(userRowNum)[1]+' '+mesText.split(' ')[1]+' '+mesText.split(' ')[2]+' '+"添加成功"
        ))
        return 0

    # if event.message.text == '簽到表':
        line_bot_api.reply_message(event.reply_token,TextMessage(text="https://docs.google.com/spreadsheets/d/1OAnZINtomnLuh89heNoRZJ94wzaShbQd-1mlEKhbl3c/edit#gid=1198036521"))
        return 0

    # if '加歌' in event.message.text:
        sh = sheet.worksheet('歌單')
        mesText = event.message.text
        try:
            textContentSplit = mesText.split(' ')[1:]
            if textContentSplit[0]=='':
                print('格式有誤')
                line_bot_api.reply_message(event.reply_token,TextMessage(text="格式有誤"))
                return 0
            textContent = [" ".join(textContentSplit)]
            textContent.append(dbid)
            textContent.append(dbtim)

        except Exception as e:
            print('無空格\n', e)
            line_bot_api.reply_message(event.reply_token,TextMessage(text="無空格"))
            return 0
        sh.append_row(textContent)
        line_bot_api.reply_message(event.reply_token,TextMessage(text="添加成功"))
        return 0
    
    if event.message.text == '歌單':
        line_bot_api.reply_message(event.reply_token,TextMessage(text="https://docs.google.com/spreadsheets/d/1OAnZINtomnLuh89heNoRZJ94wzaShbQd-1mlEKhbl3c/edit#gid=1246252573"))
        return 0
    #登錄不用if 直接進去google表單 回報確認登錄
    #遊戲進度 以及 設定一樣模式
    # if event.message.text == '登錄': #功能未完成
        if isinstance(event.source, SourceUser):
            profile = line_bot_api.get_profile(event.source.user_id)
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(
                        text='用戶名稱: ' + profile.display_name
                    ),
                    TextSendMessage(
                        text='用戶個簽: ' + profile.status_message
                    ),
                    TextSendMessage(
                        text='用戶ID: ' + "u0001"
                    )
                    ,
                    TextSendMessage(
                        text='Line_userId: ' + event.source.user_id
                    )#存入某個檔案裡面
                ]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="Bot can't use profile API without user ID"))
        return 0

    # if event.message.text == 'profile':
        if isinstance(event.source, SourceUser):
            profile = line_bot_api.get_profile(event.source.user_id)
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(
                        text='Display name: ' + profile.display_name
                    ),
                    TextSendMessage(
                        text='Status message: ' + profile.status_message
                    )
                ]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="Bot can't use profile API without user ID"))
        return 0
    return 0
    if 1:
        return
    else:
        answers =[
                "😁",
                "😂",
                "😃",
                "😄",
                "😅",
                "😆",
                "😉",
                "😊",
                "😋",
                "😌",
                "😍",
                "😏",
                "😒",
                "😓",
                "😔",
                "😖",
                "😘",
                "😚",
                "😜",
                "😝",
                "😞",
                "😠",
                "😡"
                ]
        textNum = random.randint(0, 1) #text or picture
        index = random.randint(0, len(answers) - 1)
        mesText = answers[index]
        ifNum = random.randint(0, 29)
        if "anya" in event.message.text or "安妮亞" in event.message.text or "阿妮亞" in event.message.text or "助理" in event.message.text:
           ifNum = 0 # do 100%
        if ifNum == 0:
            if textNum == 0:
                # cur = conn.cursor()
                cur.execute(
                    """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
                    ("me", dbname, mesText, dbtim, dbts )
                );
                conn.commit()
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=mesText))
            else:
                client = ImgurClient(client_id, client_secret)
                images = client.get_album_images("7aHqXX5")
                index = random.randint(0, len(images) - 1)
                url = images[index].link
                image_message = ImageSendMessage(
                    original_content_url=url,
                    preview_image_url=url
                )
                line_bot_api.reply_message(
                    event.reply_token, image_message)
        return 0               
if __name__ == '__main__':
    app.run()
