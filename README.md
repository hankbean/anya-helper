# 吃吃管家 Line Bot (Django 版本)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Visitors](https://visitor-badge.laobi.icu/badge?page_id=hankbean.anya-helper)

「吃吃管家」是一個多功能 LINE 智慧助理，整合了強大的 AI 聊天、實用的生活工具與有趣的玄學娛樂，旨在為您的日常對話帶來便利與樂趣。

## 版本說明

這是我使用 **Django** 框架重構後的版本，目的是為了利用其強大的 MTV 架構與內建功能，以獲得更好的擴展性與可維護性。

此專案的 [**原始 Flask 版本**](https://github.com/hankbean/anya-helper/tree/flask-legacy) 也可以在 `flask-legacy` 分支中找到。

## 功能亮點

- **智慧聊天互動**：支援私聊與群組聊天，能理解上下文並透過 Function Calling 自主選擇回應或保持沉默。
- **玄學娛樂功能**：提供塔羅牌占卜與 AI 解夢，為生活增添神秘色彩。
- **實用生活工具**：
  - **AI 事實查核**：幫助辨別假訊息，提供正確資訊。
  - **165 防詐騙查詢**：透過非同步網頁爬蟲，即時查詢可疑電話號碼。
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

如果您想在本機環境下執行或進行二次開發，請遵循以下 Django 標準流程。

### 1. 前置需求
- Python 3.11 或更高版本
- Git
- Pipenv (套件管理工具)

### 2. 安裝步驟
```bash
# 1. Clone 專案
git clone https://github.com/hankbean/anya-helper.git
cd anya-helper

# 2. 安裝專案依賴並進入虛擬環境
# Pipenv 會自動讀取 Pipfile 來安裝所有開發與生產所需的套件，並建立虛擬環境
pipenv install --dev
pipenv shell
```

### 3. 環境變數設定
本專案使用 `.env` 檔案來管理本地開發環境的敏感金鑰。

1.  複製 `.env.example` 檔案為 `.env`。
    ```bash
    cp .env.example .env
    ```
2.  在 `.env` 檔案中填入您自己的金鑰：
    ```env
    # .env - 本地開發環境變數

    # Django Core Settings
    DJANGO_SECRET_KEY="your-django-secret-key"
    DEBUG="True"

    # Line Bot API
    Channel_Access_Token="YOUR_LINE_CHANNEL_ACCESS_TOKEN"
    Channel_Secret="YOUR_LINE_CHANNEL_SECRET"

    # OpenAI API
    OPENAI_API="YOUR_OPENAI_API_KEY"

    # Supabase (Database)
    SUPABASE_URL="YOUR_SUPABASE_URL"
    SUPABASE_KEY="YOUR_SUPABASE_KEY"
    
    # Google Search API
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
    GOOGLE_CSE_ID="YOUR_GOOGLE_CSE_ID"

    # Imgur API
    IMGUR_CLIENT_ID="YOUR_IMGUR_CLIENT_ID"
    IMGUR_CLIENT_SECRET="YOUR_IMGUR_CLIENT_SECRET"
    IMGUR_ALBUM_ID="YOUR_IMGUR_ALBUM_ID"
    ```

### 4. 資料庫初始化
本專案使用 Django 的 ORM，在啟動前需要先進行資料庫遷移。
```bash
python manage.py migrate
```

### 5. 啟動應用程式
```bash
# 啟動 Django 開發伺服器
python manage.py runserver
```
啟動後，應用程式預設運行在 `http://127.0.0.1:8000/`。您需要設定一個 `ngrok` 之類的工具，將您的本機網址暴露給公網，並將 Webhook URL (例如 `https://your-ngrok-url.io/line_bot/callback`) 填入 LINE Developer 後台。

---

## 部署說明 (Deployment Notes)

本專案已針對 Heroku 平台進行了優化配置：

- **`Pipfile`**: Heroku 會自動偵測到 `Pipfile` 的存在，並使用 `pipenv` 來安裝所有依賴套件。同時，`Pipfile` 中的 `[requires]` 區塊也定義了專案所需的 **Python 版本**，因此無需 `runtime.txt`。
- **`Procfile`**: 定義了 Heroku 該如何使用 `gunicorn` 啟動生產環境的 WSGI 伺服器。
- **環境變數**: 所有在 `.env` 中定義的變數，在 Heroku 上都應設定於 **Config Vars** 中，以確保生產環境的安全性。

## 🛠️ 技術棧 (Tech Stack)

- **後端框架**: **Django**
- **部署伺服器**: Gunicorn
- **LINE 互動**: line-bot-sdk-python
- **AI 核心**: OpenAI API (Function Calling)
- **資料庫**: Supabase (PostgreSQL)
- **非同步網頁爬蟲**: Playwright
- **圖片儲存/處理**: Imgur API
- **環境變數管理**: python-dotenv
- **套件管理**: Pipenv

## 授權條款 (License)

本專案採用 [MIT License](https://opensource.org/licenses/MIT) 授權。