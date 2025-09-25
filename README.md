# 吃吃管家 Line Bot

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

「吃吃管家」是一個多功能 LINE 智慧助理，整合了強大的 AI 聊天、實用的生活工具與有趣的玄學娛樂，旨在為您的日常對話帶來便利與樂趣。

## 功能亮點

- **智慧聊天互動**：支援私聊與群組聊天，能理解上下文並自主選擇回應或保持沉默。
- **玄學娛樂功能**：提供塔羅牌占卜與 AI 解夢，為生活增添神秘色彩。
- **實用生活工具**：
  - **AI 事實查核**：幫助辨別假訊息，提供正確資訊。
  - **165 防詐騙查詢**：即時查詢可疑電話號碼，保護您與家人的安全。
  - **網路資料搜尋**：快速整理網路資訊與文章摘要。
- **優化使用者體驗**：採用 LINE Loading 動畫，讓等待時間在視覺上更流暢。

## 如何使用

掃描 QR Code 或點擊連結，將「吃吃管家」加入您的 LINE 好友！

![QR Code to add Line Bot](https://iili.io/KIXAvf9.md.jpg)

**手機點擊連結**：[https://lin.ee/4NgW1BU](https://lin.ee/4NgW1BU)

---

## 功能展示

### 🔮 玄學娛樂

#### 塔羅牌占卜
**指令**：`吃吃請幫我占卜，我想問[您的問題]嗎？`
![塔羅牌占卜範例](https://iili.io/K7FPFun.png)

#### AI 解夢
**使用方式**：直接向吃吃管家描述您的夢境。
![AI 解夢範例](https://iili.io/K7Fpbrg.png)

### 🛡️ 生活工具 (防詐與搜尋)

#### 假訊息糾錯 & 事實查核
![假訊息糾錯範例 1](https://iili.io/K7F5X9f.png)
![假訊息糾錯範例 2](https://iili.io/K7F4S0N.png)

#### 165 詐騙電話查詢
![165 查詢範例](https://iili.io/KlWdaz7.png)

#### 網路資料與文章搜尋
![網路搜尋範例](https://iili.io/KlWHVEb.png)

### ✨ 互動體驗

#### 群組聊天
吃吃管家在群聊中也能與成員自由互動。
![群組聊天範例](https://iili.io/K7KTQHv.png)

#### Loading 動畫
透過 `ShowLoadingAnimation` API，優化了使用者的等待體驗，讓互動更流暢。
![Loading 動畫範例](https://iili.io/K7FPvSI.png)

---

## 👨‍💻 開發者指南：安裝與設定

如果您想在本機環境下執行或進行二次開發，請遵循以下步驟。

### 1. 前置需求
- Python 3.11 或更高版本
- Git

### 2. 安裝步驟
```bash
# 1. Clone 專案
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name

# 2. 建立並啟用虛擬環境 (建議)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. 安裝依賴套件
pip install -r requirements.txt
```

### 3. 環境變數設定
您需要設定必要的 API 金鑰才能讓 Bot 正常運作。

1.  複製 `.env.example` 檔案為 `.env`。
    ```bash
    cp .env.example .env
    ```
2.  在 `.env` 檔案中填入您的金鑰：
    ```env
    # .env
    Channel_Access_Token="YOUR_LINE_CHANNEL_ACCESS_TOKEN"
    Channel_Secret="YOUR_LINE_CHANNEL_SECRET"
    OPENAI_API="YOUR_OPENAI_API_KEY"
    SUPABASE_URL="YOUR_SUPABASE_URL"
    SUPABASE_KEY="YOUR_SUPABASE_KEY"
    ```

### 4. 啟動應用程式
```bash
# 啟動 Flask 開發伺服器
flask run
```
啟動後，您需要設定一個 `ngrok` 之類的工具，將您的本機 `localhost` 網址暴露給公網，並將 Webhook URL 填入 LINE Developer 後台。

## 🛠️ 技術棧 (Tech Stack)

- **後端框架**: Flask
- **LINE 互動**: line-bot-sdk-python
- **AI 核心**: OpenAI API
- **資料庫**: Supabase (PostgreSQL)
- **網頁爬蟲**: Playwright
- **圖片儲存/處理**: Imgur API

## 授權條款 (License)

本專案採用 [MIT License](https://opensource.org/licenses/MIT) 授權。