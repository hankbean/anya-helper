import time

from bs4 import BeautifulSoup
import requests

def ptt_beauty():
    rs = requests.session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }
    rs.headers.update(headers)
    res = rs.get('https://disp.cc/b/Beauty', verify=False)

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