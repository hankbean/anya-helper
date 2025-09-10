import pytest
import app

def test_hello():
    assert app.hello() == "ok!"

# def test_hello2():
#     assert app.hello() == "oksssss!","錯誤說明可以這樣寫"

# def test_sendNormalText():
#     event = [type='message' source=GroupSource(type='group', group_id='C6ebd5c8e9ae2e5aec0106edb6c11c627', user_id='Ue146791490e8eba660a914d937be3af1') timestamp=1757099086436 mode=<EventMode.ACTIVE: 'active'> webhook_event_id='01K4DM8N16YWE0F70Y2HMZ8VWQ' delivery_context=DeliveryContext(is_redelivery=False) reply_token='6d89a18ac9e345e6af835ffebba2d456' message=TextMessageContent(type='text', id='577585494750920739', text='()啊啊啊啊', emojis=[Emoji(index=0, length=2, product_id='629863125658444ccadfada2', emoji_id='013')], mention=None, quote_token='e23oavBVlk4xA40PGSlRrbhGG8l30iD12T2oXND8pA1KzwlI6JTvdtsnruMAeBY41fqWzp7KLgVIS9G1EDN4ovGUO6S2NsejjxxD_nKA4aFSgKktP0I0tMXz8tVb9XGkdkrqGSOoHemkhAsPPsOLiw', quoted_message_id=None)]
#     assert app.sendNormalText(event, mesText)

""" # 1. 導入所有需要的類別
from linebot.v3.webhooks import (
    MessageEvent,
    GroupSource,
    TextMessageContent,
    Emoji,
    DeliveryContext,
    EventMode,
)

# 你的 app 模組 (假設它存在)
import app

def test_sendNormalText():
    # 2. 定義 'mesText' 變數
    mesText = "()啊啊啊啊"

    # 3. 用「呼叫類別建構式」的方式，一步步建立出完整的 event 物件
    #    這才是真正的 Python 程式碼
    event = [
        MessageEvent(
            type='message',
            source=GroupSource(
                type='group',
                group_id='C6ebd5c8e9ae2e5aec0106edb6c11c627',
                user_id='Ue146791490e8eba660a914d937be3af1'
            ),
            timestamp=1757099086436,
            mode=EventMode.ACTIVE,
            webhook_event_id='01K4DM8N16YWE0F70Y2HMZ8VWQ',
            delivery_context=DeliveryContext(is_redelivery=False),
            reply_token='6d89a18ac9e345e6af835ffebba2d456',
            message=TextMessageContent(
                type='text',
                id='577585494750920739',
                text="()啊啊啊啊",  # 直接使用上面定義的變數
                emojis=[
                    Emoji(
                        index=0,
                        length=2,
                        product_id='629863125658444ccadfada2',
                        emoji_id='013'
                    )
                ]
            )
        )
    ]

    # 4. 執行斷言
    #    注意：這裡假設 app.sendNormalText 會回傳一個布林值或某個可判斷真假的結果
    assert app.sendNormalText(event, "測試測試") ==  """
""" # test/test_app.py

# 假設你的原程式碼在 app.py 檔案中
import app

# 導入所有需要的 LINE SDK 類別，以便在測試中建立預期物件
from linebot.v3.webhooks import (
    MessageEvent, GroupSource, TextMessageContent, Emoji, DeliveryContext, EventMode
)
from linebot.v3.messaging import (
    ReplyMessageRequest, TextMessage, ApiResponse
)


# mocker 是 pytest-mock 提供的 special fixture
def test_sendNormalText_sends_correct_data(mocker):
    """
    # 測試：當傳入一般長度的文字時，sendNormalText 是否用正確的參數呼叫了 reply_message
"""
    # GIVEN (準備階段)
    # 1. 準備函式需要的輸入資料
    reply_token_in_test = 'a_fake_reply_token'
    text_to_send = "測試測試AAA"

    event_data = MessageEvent(
        reply_token=reply_token_in_test,
        # ... 其他 event 參數可以簡化或省略，除非你的函式邏輯會用到它們
        # 這裡為了完整性，我們先保留
        type='message',
        source=GroupSource(type='group', group_id='C...27', user_id='U...f1'),
        timestamp=1757099086436, mode=EventMode.ACTIVE, webhook_event_id='01K...',
        delivery_context=DeliveryContext(is_redelivery=False),
        message=TextMessageContent(type='text', id='577...', text='用戶傳來的訊息')
    )

    # 2. Mock 核心部分：取代真實的 API 呼叫
    # 我們需要攔截 `MessagingApi` 的 `reply_message_with_http_info` 方法
    # mocker.patch 的路徑要指向你的 app.py 中 MessagingApi 被引用的地方
    mock_reply_method = mocker.patch('app.MessagingApi.reply_message_with_http_info')
    
    # 為了讓 `with ApiClient(...)` 語法能正常運作，我們也需要 mock 它們
    mocker.patch('app.ApiClient')

    # WHEN (執行階段)
    # 3. 呼叫我們要測試的函式
    app.sendNormalText(event_data, text_to_send)

    # THEN (驗證階段)
    # 4. 斷言：驗證我們的 mock 方法是否被「正確地」呼叫了
    
    # 4.1 建立我們預期 API 應該收到的 ReplyMessageRequest 物件
    expected_request = ReplyMessageRequest(
        reply_token=reply_token_in_test,
        messages=[TextMessage(text=text_to_send)]
    )

    # 4.2 斷言 mock 方法被呼叫過一次，並且傳入的參數和我們預期的一模一樣
    mock_reply_method.assert_called_once_with(expected_request)


def test_sendNormalText_truncates_long_text(mocker):
    """
    # 測試：當傳入超長文字時，sendNormalText 是否會正確截斷文字
"""    
    # GIVEN
    reply_token_in_test = 'another_fake_token'
    # 建立一個超過 5000 字元的超長字串
    long_text = "A" * 6000
    
    event_data = MessageEvent(reply_token=reply_token_in_test, message=TextMessageContent(text='...'))

    mock_reply_method = mocker.patch('app.MessagingApi.reply_message_with_http_info')
    mocker.patch('app.ApiClient')

    # WHEN
    app.sendNormalText(event_data, long_text)

    # THEN
    # 1. 預期被截斷後的文字
    expected_truncated_text = long_text[:4950] + "\n... (因內容過長，已省略部分)"

    # 2. 建立預期的請求物件
    expected_request = ReplyMessageRequest(
        reply_token=reply_token_in_test,
        messages=[TextMessage(text=expected_truncated_text)]
    )

    # 3. 斷言 API 是用「被截斷後的文字」來呼叫的
    mock_reply_method.assert_called_once_with(expected_request) """

# test/test_app.py

import app
from linebot.v3.webhooks import (
    MessageEvent, GroupSource, TextMessageContent, DeliveryContext, EventMode
)
from linebot.v3.messaging import (
    ReplyMessageRequest, TextMessage
)

def test_sendNormalText_sends_correct_data(mocker):
    """
    測試：當傳入一般長度的文字時，sendNormalText 是否用正確的參數呼叫了 reply_message
    """
    # GIVEN (準備階段)
    reply_token_in_test = 'a_fake_reply_token'
    text_to_send = "測試測試AAA"

    event_data = MessageEvent(
        reply_token=reply_token_in_test,
        type='message',
        source=GroupSource(type='group', group_id='C...27', user_id='U...f1'),
        timestamp=1757099086436,
        mode=EventMode.ACTIVE,
        webhook_event_id='01K...',
        delivery_context=DeliveryContext(is_redelivery=False),
        # --- 修正點 ---
        # 根據 Pydantic 的錯誤回報，補上所有 TextMessageContent 的必要欄位
        message=TextMessageContent(
            type='text',
            id='a_fake_message_id',       # 補上 id
            text='用戶傳來的訊息',
            quote_token='a_fake_quote_token' # 補上 quoteToken
        )
    )

    mock_reply_method = mocker.patch('app.MessagingApi.reply_message_with_http_info')
    mocker.patch('app.ApiClient')

    # WHEN (執行階段)
    app.sendNormalText(event_data, text_to_send)

    # THEN (驗證階段)
    expected_request = ReplyMessageRequest(
        reply_token=reply_token_in_test,
        messages=[TextMessage(text=text_to_send)]
    )
    mock_reply_method.assert_called_once_with(expected_request)


def test_sendNormalText_truncates_long_text(mocker):
    """
    測試：當傳入超長文字時，sendNormalText 是否會正確截斷文字
    """
    # GIVEN
    reply_token_in_test = 'another_fake_token'
    long_text = "A" * 6000
    
    # --- 修正點 ---
    # 建立 event_data 時，一樣要滿足 MessageEvent 和 TextMessageContent 的所有必要欄位
    event_data = MessageEvent(
        reply_token=reply_token_in_test,
        type='message',
        source=GroupSource(type='group', group_id='C...27', user_id='U...f1'),
        timestamp=1757099086436,
        mode=EventMode.ACTIVE,
        webhook_event_id='01K...',
        delivery_context=DeliveryContext(is_redelivery=False),
        message=TextMessageContent(
            type='text',
            id='another_fake_id',      # 補上 id
            text='...',
            quote_token='another_fake_quote_token' # 補上 quoteToken
        )
    )

    mock_reply_method = mocker.patch('app.MessagingApi.reply_message_with_http_info')
    mocker.patch('app.ApiClient')

    # WHEN
    app.sendNormalText(event_data, long_text)

    # THEN
    expected_truncated_text = long_text[:4950] + "\n... (因內容過長，已省略部分)"
    expected_request = ReplyMessageRequest(
        reply_token=reply_token_in_test,
        messages=[TextMessage(text=expected_truncated_text)]
    )
    mock_reply_method.assert_called_once_with(expected_request)