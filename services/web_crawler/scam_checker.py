import json
import re

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def scrape_165_async(phone_number: str) -> dict:
    """
    使用 Playwright 模擬瀏覽器來查詢 165 網站，以應對 SPA 架構。
    """
    # 這是使用者在瀏覽器中實際訪問的網址
    url = f"https://165.npa.gov.tw/#/search?keyword={phone_number}&dataType=4"
    
    try:
        # 啟動 Playwright
        async with async_playwright() as p:
            # 啟動一個瀏覽器實例 (這裡使用 Chromium)
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # 前往目標網址
            await page.goto(url)
            
            # 等待查詢結果的關鍵元素出現，這是最重要的一步
            # 我們等待 app-fraud-tel-result (有結果) 或 div.text-center (查無資料) 出現
            # 等待最多 10 秒
            await page.wait_for_selector("app-fraud-tel-result, div.text-center:has-text('查無資料')", timeout=10000)
            
            # 獲取頁面渲染完成後的完整 HTML
            content = await page.content()
            
            # 關閉瀏覽器
            await browser.close()

        # 使用 BeautifulSoup 解析渲染後的 HTML
        soup = BeautifulSoup(content, "lxml")
        
        # 尋找是否有查詢結果的表格
        result_table = soup.select_one("app-fraud-tel-result table")
        
        if result_table:
            # 如果找到了表格，表示有被通報的紀錄
            details = "此號碼在 165 網站上有被通報的紀錄，風險較高。"
            # 可以嘗試從表格中提取更詳細的資訊
            first_row = result_table.select_one("tbody tr")
            if first_row:
                columns = first_row.select("td")
                if len(columns) >= 3:
                    details += f"\n通報號碼：{columns[0].text.strip()}，統計區間：{columns[1].text.strip()} ~ {columns[2].text.strip()}"
            
            return {"source": "165全民防騙網", "is_scam": True, "details": details}
        else:
            # 如果沒有找到表格，表示尚無通報
            return {"source": "165全民防騙網", "is_scam": False, "details": "目前尚無詐騙通報紀錄。"}

    except Exception as e:
        print(f"使用 Playwright 爬取 165 網站時發生錯誤: {e}")
        return {"source": "165全民防騙網", "status": "error", "message": "查詢失敗"}

async def perform_scam_phone_check(phone_number_from_ai: str, blacklist: set) -> str:
    """
    執行詐騙電話查詢的本地實作。
    整合 165 網站爬蟲和傳入的黑名單。
    """
    # cleaned_number = re.sub(r'\D', '', phone_number_from_ai)
    normalized_number = normalize_phone_for_165(phone_number_from_ai)
    
    # 2. 移除我們自己的驗證，因為任何數字組合都有可能
    if not normalized_number: # 只檢查是否為空
        return json.dumps({"status": "invalid_format", "summary": f"號碼「{phone_number_from_ai}」中不含任何數字，無法查詢。"})

    print(f"正在查詢已正規化的號碼: {normalized_number}")

    is_scam = False
    details_list = []

    # 1. 查詢傳入的黑名單 (blacklist)
    if normalized_number in blacklist:
        is_scam = True
        details_list.append("此號碼位於內部高風險黑名單中。")

    # 2. 查詢 165 網站
    result_165 = await scrape_165_async(normalized_number)
    print("result_165: ", result_165)
    if result_165.get("is_scam"):
        is_scam = True
        details_list.append(result_165.get("details"))
    elif "details" in result_165:
        details_list.append(result_165.get("details"))

    # --- 總結結果 ---
    if is_scam:
        summary = f"🚨 警告！電話號碼 {normalized_number} 具有高詐騙風險。\n查詢結果：\n- " + "\n- ".join(details_list)
        final_status = "scam_detected"
    else:
        summary = f"✅ 電話號碼 {normalized_number} 的查詢結果如下：\n- " + "\n- ".join(details_list) + "\n提醒您，即使目前無紀錄，仍請保持警惕。"
        final_status = "no_record_found"
    print("summary: ", summary)
    return json.dumps({
        "status": final_status,
        "is_scam": is_scam,
        "summary": summary
    })

def normalize_phone_for_165(phone_number_str: str) -> str:
    """
    為了適應 165 網站的查詢規則，將輸入字串清理成只剩下純數字。
    例如：'+886 912-345-678' -> '886912345678'
    """
    cleaned_number = re.sub(r'\D', '', phone_number_str)
    return cleaned_number
