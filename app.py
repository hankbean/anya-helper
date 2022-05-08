import requests
import re
import random
import configparser
from bs4 import BeautifulSoup
from flask import Flask, request, abort
from imgurpython import ImgurClient

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *


import datetime

import os
from urllib import parse
import psycopg2

import jwt
from jwt.algorithms import RSAAlgorithm
import time


verTime = "2022.Apr.03.5" # 版本
verAnswer= "回答"


parse.uses_netloc.append("postgres")
url = parse.urlparse(os.environ["DATABASE_URL"])

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
print ("Opened database successfully")

privateKey = {
  "alg": "RS256",
  "d": "NeR0jm5iAZjzLUec06WJHbzp6NmCCdZUe7VBC-00xwArHRKMpR5vwmood8pIGHiG7U0VbsUCdg9m0aun09Jepu0nJl5SC9moeo8WYZ4I6tHloBPjCqSZ4CzqRKe2-7CQbPg9jkky7XwY1zP2SrAXciq_d6KBtZW9LSJiykmK4UDZIpVv53F-C-3Dy7JICwaIffskvy4kotIIqLqZ_WfLLHaX5iH-xHJUrSxm6QKPXftai4qo3Q6XqLh_f56ibMPlIiDcYj5TbJj-rL-SIag7PkGiwrG9ANoOpKewCmx7AJo-n3saegKUo8a-vswIokEfULXSmF4NDfQNWFF7VQAVZw",
  "dp": "ju619NRD-FgxBOjaRAznnITcnHlfKm2VfvQ6WOhoyVnL_wdcGAnR3_JsW8nDI0iGkVBZk9gOqvXln5DuQD1p_GRort22kUXzobMWlTPQvY1k6Qy1jyEUt6dLoATuS0SYjxFVAsDYiQKJv587JykNYfqJGAZI4ITh6kzXgOSN53s",
  "dq": "aTiau4-wvZPCPeaEAcTmqX8M7CXwd-owhdggH6d51h3moMB-1r1qv7cjA93UMt3rrE7KFUVN6pNMK8FNsb27lSIbhPRLSigRotx3pq30sFQwPQnjEpBWFhV340Y_QXsDBlm9hQcR-2Uuj4CKVsuI8WaP0e_JW9c9z_eugS61nOs",
  "e": "AQAB",
  "key_ops": [
    "sign"
  ],
  "kty": "RSA",
  "n": "y6KMTeLbIyZONxSGZB7b7ISB8Ov2R0e2_7ziSLIDPEVBGe9rsH2Ws7LKR_6FuCxyiGyc5Mg_oVRBDBK1Ohb85b84gCLWzP5QmyXV7jDvteOBa5Vzih-jQuj9H3XI3RgNe8cJBMGizW0Z7gycsuS7v1rzjkpscOda6R-TyqnMXhTYhtYiWLV_zJOU0DPlo5aku_CQIbD-qMQJi5UfLHoQ-ithAXSWTxzEBJnZKc0vIQrtNS7lW9_HBIPbK4HgsBoNYjzxvoyog70Q5GrFEMHkUsd2a7SdAg9mworvKnfY2uaOBc5nqq69eJA5CufZrueSA9-mW1f-rsFmn0o864snhQ",
  "p": "7eztnXq43OU54jgH8EkBSkqP50dBe5spoywPqjAxUxHsJcLIOe85QDLZfRJPUjtTVpittx7Umqcz3Wy1u4DN83CyjAj015DelSqPHcoVPsezNhpMjnFBUeIFGzcscbQ_aGE_hWEyjdWBmOtzkSaozhg_UpFovKeXfZU0r5zzLy8",
  "q": "2xrAkIs5Jr8ABYmJS5zNQWceGOWcPnU2v_ufqN2lar1hfaNZ1VTTKq2NUcLhybsw7Xdq9DFRVJhKPTITh62ITshxN4_A3i6SxtPHpBlwGKtWmI--glFDdVQlQnKHyTpl1PpDtpqeUrctJBEYpgupdlppJMEP1XKxsB7U32adx4s",
  "qi": "50yV2ChH1TIJ-jUfOPocFJLoQbcPEAgkhekTKDqkOx4ljciVtfHk6bz9-Bpx7vOoFbhJCmQaQ0YuK9GzBzLpbo57APbTkDkqJm8AN2zbqOYSrvm43iFs_EcJykZYAFfaNg8-tQz-zpRejRoGn-wjkTgmJMBmZs0PZjNlqqlcsYM"
}

headers = {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "9869e446-3489-4516-a83f-ec9214ad94d0"
}

payload = {
  "iss": "1657113670",
  "sub": "1657113670",
  "aud": "https://api.line.me/",
  "exp":int(time.time())+(60 * 30),
  "token_exp": 60 * 60 * 24 * 30
}

key = RSAAlgorithm.from_jwk(privateKey)

app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")

#line_bot_api = jwt.encode(payload, key, algorithm="RS256", headers=headers, json_encoder=None)
line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])
client_id = config['imgur_api']['Client_ID']
client_secret = config['imgur_api']['Client_Secret']
album_id = config['imgur_api']['Album_ID']
API_Get_Image = config['other_api']['API_Get_Image']


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    # print("body:",body)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'ok'


def pattern_mega(text):
    patterns = [
        'mega', 'mg', 'mu', 'ＭＥＧＡ', 'ＭＥ', 'ＭＵ',
        'ｍｅ', 'ｍｕ', 'ｍｅｇａ', 'GD', 'MG', 'google',
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True


def eyny_movie():
    target_url = 'http://www.eyny.com/forum-205-1.html'
    print('Start parsing eynyMovie....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ''
    for titleURL in soup.select('.bm_c tbody .xst'):
        if pattern_mega(titleURL.text):
            title = titleURL.text
            if '11379780-1-3' in titleURL['href']:
                continue
            link = 'http://www.eyny.com/' + titleURL['href']
            data = '{}\n{}\n\n'.format(title, link)
            content += data
    return content


def apple_news():
    target_url = 'http://www.appledaily.com.tw/realtimenews/section/new/'
    head = 'http://www.appledaily.com.tw'
    print('Start parsing appleNews....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for index, data in enumerate(soup.select('.rtddt a'), 0):
        if index == 15:
            return content
        if head in data['href']:
            link = data['href']
        else:
            link = head + data['href']
        content += '{}\n\n'.format(link)
    return content


def get_page_number(content):
    start_index = content.find('index')
    end_index = content.find('.html')
    page_number = content[start_index + 5: end_index]
    return int(page_number) + 1


def craw_page(res, push_rate):
    soup_ = BeautifulSoup(res.text, 'html.parser')
    article_seq = []
    for r_ent in soup_.find_all(class_="r-ent"):
        try:
            # 先得到每篇文章的篇url
            link = r_ent.find('a')['href']
            if link:
                # 確定得到url再去抓 標題 以及 推文數
                title = r_ent.find(class_="title").text.strip()
                rate = r_ent.find(class_="nrec").text
                url = 'https://www.ptt.cc' + link
                if rate:
                    rate = 100 if rate.startswith('爆') else rate
                    rate = -1 * int(rate[1]) if rate.startswith('X') else rate
                else:
                    rate = 0
                # 比對推文數
                if int(rate) >= push_rate:
                    article_seq.append({
                        'title': title,
                        'url': url,
                        'rate': rate,
                    })
        except Exception as e:
            # print('crawPage function error:',r_ent.find(class_="title").text.strip())
            print('本文已被刪除', e)
    return article_seq


def crawl_page_gossiping(res):
    soup = BeautifulSoup(res.text, 'html.parser')
    article_gossiping_seq = []
    for r_ent in soup.find_all(class_="r-ent"):
        try:
            # 先得到每篇文章的篇url
            link = r_ent.find('a')['href']

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
    res = rs.get('https://www.ptt.cc/bbs/Beauty/index.html', verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    all_page_url = soup.select('.btn.wide')[1]['href']
    start_page = get_page_number(all_page_url)
    page_term = 2  # crawler count
    push_rate = 10  # 推文
    index_list = []
    article_list = []
    for page in range(start_page, start_page - page_term, -1):
        page_url = 'https://www.ptt.cc/bbs/Beauty/index{}.html'.format(page)
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
            article_list = craw_page(res, push_rate)
            # print u'OK_URL:', index
            # time.sleep(0.05)
    content = ''
    for article in article_list:
        data = '[{} push] {}\n{}\n\n'.format(article.get('rate', None), article.get('title', None),
                                             article.get('url', None))
        content += data
    return content


def ptt_hot():
    target_url = 'http://disp.cc/b/PttHot'
    print('Start parsing pttHot....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for data in soup.select('#list div.row2 div span.listTitle'):
        title = data.text
        link = "http://disp.cc/b/" + data.find('a')['href']
        if data.find('a')['href'] == "796-59l9":
            break
        content += '{}\n{}\n\n'.format(title, link)
    return content


def movie():
    target_url = 'http://www.atmovies.com.tw/movie/next/0/'
    print('Start parsing movie ...')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for index, data in enumerate(soup.select('ul.filmNextListAll a')):
        if index == 20:
            return content
        title = data.text.replace('\t', '').replace('\r', '')
        link = "http://www.atmovies.com.tw" + data['href']
        content += '{}\n{}\n'.format(title, link)
    return content


def technews():
    target_url = 'https://technews.tw/'
    print('Start parsing movie ...')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""

    for index, data in enumerate(soup.select('article div h1.entry-title a')):
        if index == 12:
            return content
        title = data.text
        link = data['href']
        content += '{}\n{}\n\n'.format(title, link)
    return content


def panx():
    target_url = 'https://panx.asia/'
    print('Start parsing ptt hot....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for data in soup.select('div.container div.row div.desc_wrap h2 a'):
        title = data.text
        link = data['href']
        content += '{}\n{}\n\n'.format(title, link)
    return content

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
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
   
   

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.type == "sticker":
        print ("say hiiiiiii")
        mesFace = [
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
        mesText = mesFace[random.randint(0, len(mesFace)-1)]
        # ifNum = random.randint(0, 1)
        # if ifNum == 0:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text = mesText)
        )

        # return 0
    cur = conn.cursor()
    # cur.execute('''CREATE TABLE MESSAGE
    #        (ID TEXT      NOT NULL,
    #        NAME           TEXT    NOT NULL,
    #        MES            TEXT     NOT NULL,
    #        TIM        TEXT);''')
    # print ("Table created successfully")
    print("**********")
    dbtim = datetime.datetime.fromtimestamp(
                event.timestamp / 1000.0 + 28800
            ).strftime('%Y-%m-%d %H:%M:%S.%f')
    dbts = event.timestamp
    dbmes = event.message.text
    if isinstance(event.source, SourceUser):
        profile = line_bot_api.get_profile(event.source.user_id)
        logMes = profile.display_name + ": " + event.message.text + "[time: " + str(event.timestamp) + "]"
        print(logMes)
        # f = open('mesLogaa.txt','a')
        # f.write(logMes)
        dbid = event.source.user_id
        dbname = profile.display_name
        str(event.timestamp)
        cur.execute(
            """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
            (dbid, dbname, dbmes, dbtim, dbts )
        );
        conn.commit()
    else:
        if isinstance(event.source, SourceGroup):
            # profile = line_bot_api.get_profile(event.source.group_id)
            dbid = event.source.group_id
            dbname = "group"
            # dbtim = str(event.timestamp)
            cur.execute(
                """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s, %s)""",
                (dbid, dbname, dbmes, dbtim, dbts )
            );
            conn.commit()
        elif isinstance(event.source, SourceRoom):
            # profile = line_bot_api.get_profile(event.source.room_id)
            dbid = event.source.room_id
            dbname = "room"
            # dbtim = str(event.timestamp)
            cur.execute(
                """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s, %s)""",
                (dbid, dbname, dbmes, dbtim, dbts )
            );
            conn.commit()

    print("event.message.text:", event.message.text)
    print("event.reply_token:", event.reply_token)
    print("event.source.user_id:", event.source.user_id)
    # conn.close()

    if event.message.text == "eyny":
        content = eyny_movie()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "蘋果即時新聞":
        content = apple_news()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "PTT 表特版 近期大於 10 推的文章":
        content = ptt_beauty()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "抽正妹":
        client = ImgurClient(client_id, client_secret)
        images = client.get_album_images(album_id)
        index = random.randint(0, len(images) - 1)
        url = images[index].link
        image_message = ImageSendMessage(
            original_content_url=url,
            preview_image_url=url
        )
        line_bot_api.reply_message(
            event.reply_token, image_message)
        return 0
    if event.message.text == "牌" or event.message.text == "抽":
        client = ImgurClient(client_id, client_secret)
        images = client.get_album_images("jAqXRhh")#client.get_album_images("l8aRa")
        index = random.randint(0, len(images) - 1)
        url = images[index].link
        image_message = ImageSendMessage(
            original_content_url=url,
            preview_image_url=url
        )
        line_bot_api.reply_message(
            event.reply_token, image_message)
        return 0
    if event.message.text == "抽牌圖test":
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
    if event.message.text == "隨便來張正妹圖片":
        image = requests.get(API_Get_Image)
        url = image.json().get('Url')
        image_message = ImageSendMessage(
            original_content_url=url,
            preview_image_url=url
        )
        line_bot_api.reply_message(
            event.reply_token, image_message)
        return 0
    if event.message.text == "近期熱門廢文":
        content = ptt_hot()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "即時廢文":
        content = ptt_gossiping()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "近期上映電影":
        content = movie()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "科技新報":
        content = technews()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "PanX泛科技":
        content = panx()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "開始玩":
        buttons_template = TemplateSendMessage(
            alt_text='開始玩 template',
            template=ButtonsTemplate(
                title='選擇服務',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/xQF5dZT.jpg',
                actions=[
                    MessageTemplateAction(
                        label='新聞',
                        text='新聞'
                    ),
                    MessageTemplateAction(
                        label='電影',
                        text='電影'
                    ),
                    MessageTemplateAction(
                        label='看廢文',
                        text='看廢文'
                    ),
                    MessageTemplateAction(
                        label='正妹',
                        text='正妹'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0
    if event.message.text == "新聞":
        buttons_template = TemplateSendMessage(
            alt_text='新聞 template',
            template=ButtonsTemplate(
                title='新聞類型',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/vkqbLnz.png',
                actions=[
                    MessageTemplateAction(
                        label='蘋果即時新聞',
                        text='蘋果即時新聞'
                    ),
                    MessageTemplateAction(
                        label='科技新報',
                        text='科技新報'
                    ),
                    MessageTemplateAction(
                        label='PanX泛科技',
                        text='PanX泛科技'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0
    if event.message.text == "電影":
        buttons_template = TemplateSendMessage(
            alt_text='電影 template',
            template=ButtonsTemplate(
                title='服務類型',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/sbOTJt4.png',
                actions=[
                    MessageTemplateAction(
                        label='近期上映電影',
                        text='近期上映電影'
                    ),
                    MessageTemplateAction(
                        label='eyny',
                        text='eyny'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0
    if event.message.text == "看廢文":
        buttons_template = TemplateSendMessage(
            alt_text='看廢文 template',
            template=ButtonsTemplate(
                title='你媽知道你在看廢文嗎',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/ocmxAdS.jpg',
                actions=[
                    MessageTemplateAction(
                        label='近期熱門廢文',
                        text='近期熱門廢文'
                    ),
                    MessageTemplateAction(
                        label='即時廢文',
                        text='即時廢文'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0
    if event.message.text == "正妹":
        buttons_template = TemplateSendMessage(
            alt_text='正妹 template',
            template=ButtonsTemplate(
                title='選擇服務',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/qKkE2bj.jpg',
                actions=[
                    MessageTemplateAction(
                        label='PTT 表特版 近期大於 10 推的文章',
                        text='PTT 表特版 近期大於 10 推的文章'
                    ),
                    MessageTemplateAction(
                        label='來張 imgur 正妹圖片',
                        text='來張 imgur 正妹圖片'
                    ),
                    MessageTemplateAction(
                        label='隨便來張正妹圖片',
                        text='抽正妹'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0
    if event.message.text == "#測試":
        buttons_template = TemplateSendMessage(
            alt_text='目錄 template',
            template=ButtonsTemplate(
                title='選擇服務',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/kzi5kKy.jpg',
                actions=[
                    MessageTemplateAction(
                        label='開始玩',
                        text='開始玩'
                    ),
                    URITemplateAction(
                        label='影片介紹 阿肥bot',
                        uri='https://youtu.be/1IxtWgWxtlE'
                    ),
                    URITemplateAction(
                        label='如何建立自己的 Line Bot',
                        uri='https://github.com/twtrubiks/line-bot-tutorial'
                    ),
                    URITemplateAction(
                        label='聯絡作者',
                        uri='https://www.facebook.com/TWTRubiks?ref=bookmarks'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0


    if event.message.text =="抽牌" or event.message.text =="抽大牌" or event.message.text =="六芒星":
                        
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

        if event.message.text =="六芒星" or event.message.text == "#2":
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
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
                ("me", dbname, mesText, dbtim, dbts )
            );
            conn.commit()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=mesText))
        else:
            ifNum = random.randint(0, 78-1)
            if event.message.text =="抽大牌" or (ifNum >= (1-1) and ifNum < (22-1)):
                mesText = turn[random.randint(0, len(turn)-1)] + majorArcana[random.randint(0, len(majorArcana)-1)]
            else:
                mesText = turn[random.randint(0, len(turn)-1)] + minorArcanaName[random.randint(0, len(minorArcanaName)-1)] +\
                    minorArcanaNum[random.randint(0, len(minorArcanaNum)-1)]
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
                ("me", dbname, mesText, dbtim, dbts )
            );
            conn.commit()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=mesText))
        return 0

    if event.message.text == "#today":
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
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
            ("me", dbname, mesText, dbtim, dbts )
        );
        conn.commit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=mesText
            )
        )
        return 0

    if event.message.text == "骰子卡":
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
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
            ("me", dbname, mesText, dbtim, dbts )
        );
        conn.commit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mesText))
        return 0

    if event.message.text == "進階骰子卡":

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
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
            ("me", dbname, mesText, dbtim, dbts )
        );
        conn.commit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mesText))
        return 0

    if event.message.text == "不負責任猜題":
        answers = [
            "A",
            "B",
            "C",
            "D",
            "我也不知道"
        ] 
        mesText = str(answers[random.randint(0, len(answers)-1)])
        cur = conn.cursor()
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

    if event.message.text == "#list" or event.message.text == "說明" or event.message.text == "文大吃吃" or event.message.text == "吃吃精靈" or event.message.text == "文大吃吃精靈" or event.message.text == "吃吃":
        userid = event.source
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="指令清單: \n\n抽 or 牌\n抽牌\n抽大牌\n六芒星\n六芒星說明\n骰子卡\n進階骰子卡\n"+\
                "吃什麼\n中二\n侑子 or 次元魔女\n靈數占卜\n不負責任猜題\n#點歌\n#講笑話\n\n作者\n版本"
            )
            # 召喚
            #【人名、綽號】(例如[豆豆])
        )
        return 0

    if event.message.text == "#未開發功能":
        userid = event.source
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="指令清單: \n侑子的寶物占卜\n靈數"
            )
        )
        return 0

    if event.message.text == "#devmode":#隱藏功能
        userid = event.source
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="指令清單: \n#測試\n抽正妹\n登錄\n#today\n#未開發功能"
            )
        )
        return 0

    # 以下用檔案儲存

    if event.message.text == "作者":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="本機器人由 『豆神教文大總部部長兼教主』 豆豆製作"))
        return 0

    if event.message.text == "#回答":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=verAnswer))

        return 0

    if event.message.text == "版本":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=verTime))

        return 0

    # if event.message.text == "豆豆" or event.message.text == "吳浩宇" or event.message.text == "痘痘"  or event.message.text == "豆神":
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="我是豆神!!")) 
    #         # TextSendMessage(text="我是豆神!!\n...\n吃吃精靈是我孩子，不要玩壞她...")) 
    #     return 0

    # if event.message.text == "祥瑀" or event.message.text == "黃祥瑀":
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="約炮小王子")) 
    #     return 0

    # if event.message.text == "于姿婷" or event.message.text == "黃玥萱":
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="烤土司小公主")) 
    #     return 0

    # if event.message.text == "博榮" or event.message.text == "榮榮":
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="封杯小王子")) 
    #     return 0

    # if event.message.text == "躍萱" or event.message.text == "黃躍萱":
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="黃色洨話冠軍錦標賽第一屆傳承人")) 
    #     return 0

    # if event.message.text == "萱萱":
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="你找躍萱還是玥萱")) 
    #     return 0

    # if event.message.text == "大腸包小腸":
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="チンチン大きいです")) 
    #     return 0

    # if event.message.text == "雅慈":
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="她是智障...怎麼了嗎？")) 
    #     return 0

    # if event.message.text == "文大吃吃" or event.message.text == "吃吃精靈" or event.message.text == "文大吃吃精靈" or event.message.text == "吃吃":
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="額咪啊")) 
    #     return 0

    if event.message.text == "六芒星說明":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="牌陣說明: \n              過去\n對方心態          困難點\n              " +\
                "結論\n   未來               現在\n          自己的心態\n全局暗示\n(對方心態)可以換成(環境狀況)"
            )
        ) 
        return 0

    if event.message.text == "吃什麼" or event.message.text == "吃啥":
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
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mesText))
        return 0

    if event.message.text == "#點歌" or event.message.text == "唱歌" or event.message.text == "ktv" or "歌" in event.message.text:
        answers = [
            "年少有為-李榮浩",
            "體面-于文文 (Kelly)",
            "有一種悲傷-A-Lin",
            "說散就散-潘嘉麗 & 何維健",
            "演員-薛之謙",
            "漂向北方 (feat. 王力宏)-黃明志",
            "追光者-岑寧兒",
            "那些你很冒險的夢-林俊傑 JJ Lin",
            "倒數-G.E.M.鄧紫棋",
            "告白氣球-周杰倫",
            "家家酒-家家（JiaJia）",
            "光年之外-G.E.M.鄧紫棋",
            "怪美的-蔡依林",
            "辣台妹 (Hot Chick)-頑童 MJ116",
            "泡沫-G.E.M.鄧紫棋",
            "小幸運-田馥甄 (Hebe)",
            "怎麼了 (What's Wrong)-Eric 周興哲",
            "生僻字-陳柯宇",
            "腦公 (Hubby)-蔡依林",
            "騙吃騙吃 (Pian Jia Pian Jia)-頑童MJ116",
            "玫瑰少年 (Womxnly)-蔡依林 (Jolin Tsai)",
            "來自天堂的魔鬼 (Away)-G.E.M.鄧紫棋",
            "走到飛-熊仔 (Kumachan), 大支 (Dwagie), 呂士軒 (TroutFresh), ØZI, 吳卓源 (Julia Wu), Barry",
            "親愛的無情孫小美-茄子蛋",
            "終於勇敢了 (Brave)-袁詠琳 (Cindy Yen)",
            "再見煙火 (Goodbye Firework)-卓義峯 (Yifeng Zhuo) ",
            "不為誰而作的歌 (Twilight)-林俊傑 (JJ Lin)",
            "偉大的渺小-林俊傑 (JJ Lin)"
        ]
        mesText = answers[random.randint(0, len(answers)-1)]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mesText))
        return 0

    if event.message.text == "#講笑話" or "笑" in event.message.text or "哈" in event.message.text or "呵" in event.message.text or "廠" in event.message.text or "ㄏ" in event.message.text:
        answers = [
            "電影大亨決心製作一部有史以來規模最偉大的巨片『我要動用前所未見的陣容來演那戰爭場面。』\n\n他揚言『雙方各用兩萬五千名臨時演員。』\
            \n\n『那好極了！』導演半信半疑地說『可是，我們怎樣付得起那麼多錢給他們呢？』\n\n『計劃的妙處就是，』大亨回答，『我們要用真槍實彈。』",
            "計程車司機闖紅燈，乘客倒抽了一口氣。『別擔心。』司機說，『我哥哥總是這樣。』\n\n過了一個街口，司機在綠燈前停車。\
            \n\n『為什麼現在又停車了？』乘客問\n\n『我哥哥可能從對面開來！』",
            "做父親的帶小兒子到野外露營，要他體驗簡單生活。\n\n父親把兩手伸入山澗，捧起水來時，孩子目瞪口呆喊道『爹，你不會是要喝吧？』\
            \n\n『當然要喝』父親說著就把手裡捧著的水咕嚕喝下肚。\n\n『哎呀，爹』孩子說『我說的不是水，而是水裡的蝌蚪。』",
            "有一天小明和媽媽在客廳看電視，突然門鈴作響，媽媽跑去開門，來了一位陌生男人，這時小明也跟了過來，媽媽便對小明說：『叫爸爸！』\
            \n\n小明心理在想，很奇怪，我為何要叫他爸爸？所以小明不出聲，這時媽媽看小明不出聲，又大聲對小明說：『快叫爸爸！』\
            \n\n小明還是不肯出聲，這時媽媽生氣了，打了小明一巴掌並又對他說：『快叫爸爸！』這時小明只好哭著對陌生人喊：『爸爸........』\
            \n\n這時媽媽哭笑不得地對小明說：『誰叫你叫他爸爸呀！我是叫你去房間叫你爸爸出來繳電費啦！』",
            "在成功嶺集訓的某一天，正在上基本教練時，有一個大頭兵突然尿急，所以就跑過去向班長說：『報告班長，我想上二號。』\
            \n\n結果班長若無其事的大喊一聲：『二號過來，有人想上你！』",
            "丈夫和我走到購物廣場的許願池前。我拋下一個錢幣並許下一個願。\n\n丈夫隨即也從口袋掏出一個錢幣拋下去，我問他許了什麼願。\
            \n\n『我的願望是』他莞爾地說，『我付得起你剛才願望得到那件東西的價錢。』",
            "辦公室的主任做事非常刻板，每有指示，總要寫在紙上，並要下屬簽收。一天，他要在他的房間安裝一排軸架，工人用電鑽在牆壁上鑽孔"\
            +"，聲音非常刺耳。同事剛從外面回來，吃驚的低聲向旁邊的人說：『我的天，他現在要把指示刻在牆壁上了。』",
            "先生十分迷信，一點小事他就心神不寧。\n\n一天，下班回來，他愁眉苦臉地對我說『我的右眼跳了一個下午了，不知是什麼原因？』\
            \n\n『跳！跳！跳！』我怒不可遏，大聲對他吼叫。\n\n他許久沒有作聲，過了一會兒，他笑道：『太太，我知道我的右眼為什麼跳了。』",
            "兩個闊別多年的老同學在街上偶然偶見。\n\n甲開口就說：『你一定結婚了！』乙驚奇地問他是怎麼知道的。\
            \n\n『瞧你的衣服熨得多挺』甲答道『你以前不是這個樣子的』\n\n『可不是？』乙無奈地說，『這是我太太叫我熨的。』",
            "孩子第一天上學回來，父親問他可喜歡上學；\n\n孩子說：『我喜歡去上學，也喜歡放學，可是不喜歡中間的時間。』"
        ]
        if random.randint(0, 10)==0:
            mesText = "笑屁喔"
        else:
            mesText = answers[random.randint(0, len(answers)-1)]
        #line_bot_api.reply_message(
        #    event.reply_token,
        #    TextSendMessage(text=mesText))
        return 0

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
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
            ("me", dbname, mesText, dbtim, dbts )
        );
        conn.commit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=mesText))
        return 0

    if event.message.text == '登錄': #功能未完成
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

    if event.message.text == 'profile':
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

    else:
        answers =[
                # "在你面前閉氣的話，就會不能呼吸喔",
                # "跟你在一起時，回憶一天前的事，就像回想昨天的事情",
                # "二個人比一個人還多唷",
                "El Psy Congroo！",
                # "隐藏着黑暗力量的钥匙啊!",
                # "我要代表月亮，消灭你！~",
                "既然你誠心誠意的發問了,我們就大發慈悲的告訴你,為了防止世界被破壞,為了守護世界的和平,貫徹愛與真實的邪惡,可愛又迷人的反派角色,武藏！小次郎！我們是穿梭在銀河中的火箭隊,白洞、白色的明天正等著我們,就是這樣喵！",
                # "你不在的這十二個月，對我來說就如同一年般長",
                # "跟你通話的那個晚上，確實聽到了你的聲音",
                # "不知道為什麼，把眼睛蒙上後什麼都看不到",
                # "大部分的雞蛋料理，都要用上雞蛋喔",
                # "在非洲，每一分鐘就有60秒過去",
                # "出生時，大家都是裸體的喔",
                # "直線七秒很簡單啊 我三秒就過了",
                # "每對父母平均一人有一顆睪丸",
                "人被殺，就會死",
                # "台灣競爭力低落，在美國就連小學生都會說流利的英語",
                # "南半球的一隻蝴蝶拍了拍翅膀 他就上升了一點點",
                # "不要怨恨自己沒幹到正妹 連正妹自己都沒幹過自己",
                "愉悅！",
                "w",
                # "那天看中醫 醫師問我 是不是冬天都會感到特別冷 喝太多水就想尿尿",
                # "每當你往上踩一層階梯，你與天空的距離就會縮短",
                # "誰能知道這18歲的少女，4年前居然才14歲",
                # "為什麼自古以來紅顏多薄命呢 因為根本沒人在乎醜的人活多久",
                # "為什麼襪子總會不見一隻 因為不見兩隻你根本不會發現",
                # "根據研究，在北京呼吸霾霧很可怕，每過1小時，會折損3600秒的壽命",
                # "戒菸很簡單，我已經戒過好幾次了",
                # "當黑人演員很慘，他們永遠只能演黑人",
                # "人要是死了 那就真的死了",
                # "明天過了，後天就會來到",
                # "有些東西就是要在打折的時候買比較便宜",
                # "人就跟樹一樣 你拿斧頭砍他 他就會死掉",
                # "據統計，未婚生子的人數中有高機率為女性",
                # "當你的左臉被人打，那你的左臉就會痛",
                # "聽見你的名字時，會先想到你的樣子。",
                # "只要跟你在一起，每天就是Everyday！",
                # "放棄的話，就代表Give UP了喔！",
                # "對今天解決不了的事情 不要太擔心 因為明天也解決不了",
                # "心理學發現，聰明的人學東西比較快",
                "世上無難事 只要肯放棄",
                # "努力不一定成功 但不努力一定很爽",
                # "如果你氣憋得夠久 就可以睡到永遠",
                # "統計顯示，所有的父母的年齡都比他們的親生孩子更大，而至今沒有任何科學研究去解釋這件事的原因。",
                # "在美國，如果你不吃中餐，就會餓",
                # "聽說20歲就可以交到女朋友了，現在我完成一半了，我20歲",
                # "人如果半夜睡不著覺，就會變得格外清醒",
                # "當你在洗澡時，有高機率是裸體",
                "若要人不知，除非你不要跟他講",
                "千年之後的你會在哪裡，身邊有怎樣風景",
                "我可以跟在你身後，像影子追著光夢遊",
                "放棄規則，放縱去愛，放肆自己，放空未來",
                "我們的愛，過了就不再回來，直到現在，我還默默的等待",
                "我只想要拉住流年，好好地說聲再見，遺憾感謝都回不去昨天",
                "早安",
                "午安",
                "晚安",
                "該睡囉",
                "開心",
                "傷心",
                "吃飯去",
                "當你長久凝視深淵時，深淵也在凝視你。",
                "愚昧無知是一切痛苦之源。",
                "高貴的靈魂，是自己尊敬自己。",
                "你的良知在說什麼？——你要成為你自己。",
                "生活是一面鏡子，我們努力追求的第一件事，就是從中辨認出自己。",
                "人類的生命，不能以時間長短來衡量，心中充滿愛時，剎那即永恆!--真的是不能以時間長短來衡量的。",
                "最輕蔑人類的人，即是人類的最大恩人。",
                "沒有事實，只有詮釋。",
                "這世上沒有偶然，有的，只是必然。",
                "現世為夢，夜夢為真。",
                "決心和誠意，是為了達到某種目的必備的東西。",
                "被知道名字，就等於被對方掌握了靈魂的一部分，被知道了生日，就等於是被知道了過去的經歷和未來的前程。",
                "雖然這個世上有很多不可思議之事，但不管多麼古怪、多麼稀奇的事，只要沒有人在，只要沒有人看見，只要與人無關的話——就只不過是「現象」，瞬間即逝的事。人才是這個世界上最不可思議的事物。",
                "思想，語言是會束縛人的東西，不但自己的會束縛自己，別人的也會束縛自己。",
                "你不是只屬於你自己的，這個世界上單一的存在是不存在的，大家都會與某人產生關係,或共有某些東西，所以無法自由，所以才有趣，才悲傷，才讓人放不下。",
                "人們往往會否定無法理解，無法掌握的事，不合乎自己所期盼世界的事物，就會被認定為不好的，實事求是的說不知道，明明是那麼簡單的事。",
                "凡事都不能無中生有，實現願望一定是要有補償，或者說是付出代價。",
                "人的道路是沒有中斷……而且一直聯系在一起的東西，不管是多麼渺小的事件！比方說，不管那是多麼短暫的時間，就算沒有殘留在記憶中，也沒有留下任何記錄，只要是曾經締結過的緣分……就不會消失！",
                "越是說“不能打開”，人類就越會想要打開。自以為破壞約定所招致的災難，絕對不會降臨在自己身上。沒有人可以例外……可以超乎一切事物之外啊！",
                "所謂世界啊，雖然看起來無限寬廣，其實卻很小，只存在於自己能夠看到的範圍，能夠觸摸到的範圍，能夠感覺到的範圍之內，世界并不是從最初就存在的，而是自己創造出來的。",
                "所謂的「戒掉」，是指「全部」「徹底」，什麼「一下子」，「一點點」，「一瞬」，都一樣是在「做」。",
                "即使在一方看來是無足輕重的事情，但在另一方看來可能就成了重大事件， 而且大多數情況下，跟加害方相比，受害方損失更大。 「沒什麼大不了的」這種話只有當事者以外的才會說。 怨恨這種東西，是很容易招來的呢！",
                "占卜啊，是占卜者和被占卜者之間所進行的「交換」，占卜師必須回應被占卜的人所尋求的占卜結果，盡自己所能的所有能力，必須傾盡全力。雖然不管是什麼職業都一樣，但是看不到就說謊，或者假裝自己好像具備自己所沒有的能力，這對真心想占卜的顧客來說，是很失禮的。不，因為占卜關系到別人的前程命運，所以不是失禮就能了事的，正因如此，真正的占卜師，會在占卜時堵上自己的前途。",
                "人生的道路是一直連在一起，而且沒有中斷的東西。",
                "對於被給予的東西，必須要付出與其相當的報酬，也就是代價。不能給的太多，也不能拿的太多。不多也不少的，平等的。否則的話，就會受傷。現世的身體，星世的命運，天世的靈魂。",
                "沒錯，可怕吧？「語言」一旦說出口就收不回來，也不可能取消，而且也不知道它對人類的束縛有多強烈，人類持續地使用着那種枷鎖。",
                "人類的情緒是有缺點的，已經失去的感情，雖然可以再一次的培育，但是可能會花很多的時間。",
                "她的習慣要她自己去發現，必須她自己主動想要去改過來才行。",
                "要想獲得幸福就必須要有與之匹配的能力。",
                "人的潛在能力和自己的意識無關。",
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
        index = random.randint(0, len(answers) - 1)
        mesText = answers[index]
        ifNum = random.randint(0, 29)
        # if event.source.user_id != "Ua3c836397c7cb7f0a3df9df7d16e2be1":
        if ifNum == 0:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO MESSAGE (ID,NAME,MES,DATETIME,TIMESTAMP) VALUES (%s, %s, %s, %s ,%s)""",
                ("me", dbname, mesText, dbtim, dbts )
            );
            conn.commit()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=mesText))
        # if event.source.user_id == "Ua3c836397c7cb7f0a3df9df7d16e2be1":
        #     if ifNum == 0:
        #         line_bot_api.reply_message(
        #             event.reply_token, [
        #                 TextSendMessage(
        #                     text="感恩豆神！讚歎豆神！"
        #                 ),
        #                 TextSendMessage(
        #                     text=mesText
        #                 )
        #             ]
        #         )
        #     else:
        #         line_bot_api.reply_message(
        #             event.reply_token,
        #             TextSendMessage(
        #                 text="感恩豆神！讚歎豆神！"
        #             )
        #         )
        # else:
        #     if ifNum == 0:
        #         line_bot_api.reply_message(
        #             event.reply_token,
        #             TextSendMessage(
        #                 text=mesText
        #             )
        #         )
        return 0
                            

if __name__ == '__main__':
    app.run()
