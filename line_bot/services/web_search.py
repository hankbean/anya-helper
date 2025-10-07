import httpx
import json
import os
from django.conf import settings

async def perform_web_search(query: str) -> str:
    """
    使用 Google Custom Search API 執行網路搜尋，並回傳格式化的摘要結果。
    """

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": settings.GOOGLE_API_KEY,
        "cx": settings.GOOGLE_CSE_ID,
        "q": query,
        "num": 5  # 只獲取前 5 筆結果
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()
        
        search_results = response.json()
        
        if "items" not in search_results or not search_results["items"]:
            return json.dumps({"status": "no_results", "summary": "網路搜尋沒有找到相關結果。"})

        # 將搜尋結果格式化成乾淨的摘要字串
        summary = "以下是網路搜尋到的相關資訊摘要：\n\n"
        for i, item in enumerate(search_results["items"]):
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "").replace("\n", " ")
            summary += f"【結果 {i+1}】\n標題：{title}\n摘要：{snippet}\n連結：{link}\n\n"
        
        print(summary.strip())
        return json.dumps({"status": "success", "summary": summary.strip()})

    except Exception as e:
        print(f"網路搜尋時發生錯誤: {e}")
        return json.dumps({"status": "error", "message": "搜尋服務暫時無法使用。"})