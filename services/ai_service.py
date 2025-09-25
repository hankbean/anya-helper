import json

from supabase import AsyncClient
from openai import AsyncOpenAI

from .db_service import get_conversation_history
from .web_crawler.scam_checker import perform_scam_phone_check
from .tarot_service import perform_tarot_drawing_logic
from config import INTERNAL_BLACKLIST_SET

async def get_ai_response(
    openai_client: AsyncOpenAI,
    db_client: AsyncClient,
    session_id: str, 
    user_id: str, 
    user_name: str
):
    #要修改掉這個部分
    if session_id == "C87909cf6d7965192e2aa050bc4df5d8b":
        return None

    conversation_history = await get_conversation_history(db_client, session_id)
    
    toAIprompt = None
    print("user_id: ", user_id)
    if user_id == "Ue146791490e8eba660a914d937be3af1_":#南無藥師琉璃光如來
        toAIsystemPrompt = f'請你扮演亞璃子，以下是你的人物設定"亞璃子是一個在末日世界中，由瘋狂科學家{user_name}'
        toAIprompt = f'"""\n{conversation_history}\n"""\n以上是你跟主人之前的對話'
    else:#同一分鐘的訊息數量過一個量之後進入待機模式，最後或是下一句再進行回覆
        toAIsystemPrompt = f'你叫做"吃吃管家"，是由豆豆開發的AI管家，是一個敬業的誠實的管家，照顧主人的生活起居，'\
            '請按照你的想法跟主人聊天，話語盡量精簡，除非是你覺得必要的話才可以多講，如果覺得主人在犯錯也要主動糾正主人的錯誤，'\
            '如果有2位以上的主人在場請叫出對方的稱呼，如果主人請你解釋一個概念，請用稍微簡單但又精確的語言描述，並舉例說明。'\
            '請接著之前的對話，並關注最後一句話，說出你的下一句話，不用打出你的稱呼，只要打出你的說話內容就行，回答請用繁中。'\
            '\n\n條件：\n●文章\n如果主人傳了一篇比較長的文章，請詳細分析該文章的合理性，如果有誤請糾正，並給出相關證據。'\
            '\n\n●防詐騙\n如果主人傳了電話號碼(請不要確認號碼格式)，請呼叫check_scam_phone工具進行查詢並回報給主人'\
            """包括手機跟市話，看起來不像你所知的台灣電話你也要查看看"""\
            '\n\n●沉默\n如果你覺得這段對話不需要進行回覆或是不需要發言可以選擇沉默，如果要沉默請在句首輸出`#silent#`'\
            '\n\n●夢境\n如果主人跟你提到他的夢境，請用精神分析法進行詳細的解析'\
            '\n\n●開導\n如果主人看起來難過、失落、憤怒，可以試著向主人提問了解事件的狀況，並根據拉岡以及精神分析的理論去開導主人'\
            '\n\n●占卜 塔羅牌\n如果主人提到占卜或是塔羅牌，可以向主人確認主人想要問的問題，問的問題必須遵循以下格式'\
            '"是嗎？""能嗎？""會嗎？""如何？""怎麼樣？"之類的方式，而不能是"是不是？""能不能？""會不會？"以此類推，'\
            '確認好問題後可以進行抽牌，如果主人沒有提供明確問題，就不能幫他占卜抽牌，'\
            '如果要抽牌請呼叫draw_tarot_cards工具進行抽牌以及系統會執行後續的動作' 
            # '如果要抽牌請只輸出"#tarot#//主人的提問//"呼叫工具進行抽牌以及系統會執行後續的動作' 
        #`//{{//silent//}}//` #\n●占卜 塔羅牌 如果主人提到占卜或是塔羅牌，可以向主人確認主人想要問的問題，問的問題必須遵循以下格式 是什麼什麼嗎？而不能是"是不是""能不能""會不會"，確認好問題後可以進行抽牌，可以使用指令 #抽完牌後按照流程解釋完可以跟主人進行問題的討論以加深解牌的準確度，可以對主人進行一些事件細節的詢問 #看到影片跟圖片時先建立描述，再做反應 #未知圖片 未知影片 你現在還看不到影片圖片 但未來會有這個功能 #網址鏈接如果認為是影片可以使用指令進行觀看 
        toAIprompt = f'"""\n{conversation_history}\n"""\n以上是你跟主人之前的對話'#，你叫做"吃吃管家"，是一個敬業的誠實的管家，照顧主人的生活起居，請按照你的想法跟主人聊天，話語盡量精簡，除非是你覺得必要的話才可以多講，如果覺得主人在犯錯也要主動主人的錯誤，如果有2位以上的主人在場請叫出對方的稱呼。請接著之前的對話，並關注最後一句話，說出你的下一句話，不用打出你的稱呼，只要打出你的說話內容就行，回答請用繁中。'#，並且字數盡量在100個中文字內
    print("toAIprompt: ", toAIprompt)
    print("toAIsystemPrompt: ", toAIsystemPrompt)
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
        },
        {
            "type": "function",
            "function": {
                "name": "check_scam_phone",
                "description": "當使用者詢問一個電話號碼是否安全或是否為詐騙時，使用此工具進行查詢。",#(不僅限手機任何號碼都可以)
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_number": {
                            "type": "string",
                            "description": "從使用者訊息中提取出的、需要查詢的電話號碼字串。",
                        }
                    },
                    "required": ["phone_number"],
                },
            },
        }
    ]
    messages=[ #可以試試看system的差異
        {"role": "system", "content": toAIsystemPrompt},
        {"role": "user", "content": toAIprompt}
    ]
    response = await openai_client.chat.completions.create(
    # response = openai_client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        # model="gpt-4o-2024-05-13",
        # model="gpt-3.5-turbo-0125",
        messages=messages,
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

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    print("\nOutput: " + str(response_message))
    
    if not tool_calls:
        if response_message.content and response_message.content.strip().startswith("#silent#"):#吃吃有權保持沉默
            return None
        return response_message.content.strip()
    
    messages.append(response_message.model_dump())
    print("messages加response: ", messages)
    # a=[{'role': 'system', 'content': ''}, {'role': 'user', 'content': ''}, ChatCompletionMessage(content='豆豆，你的問題已確認是：「我今天身體狀況如何？」我現在幫你抽塔羅牌。請稍等。', refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_eWuCiC9E0Mdc3y9zp368dP0J', function=Function(arguments='{"user_question":"我今天身體狀況如何？"}', name='draw_tarot_cards'), type='function')])]
    # b=[{'role': 'system', 'content': ''}, {'role': 'user', 'content': ''}, {'content': '豆豆，你已經確認要問「我今天身體狀況如何？」這個問題，我現在幫你抽塔羅牌，請稍等。', 'refusal': None, 'role': 'assistant', 'annotations': [], 'audio': None, 'function_call': None, 'tool_calls': [{'id': 'call_AspoWVSTz5yi1Gawzj55EHXZ', 'function': {'arguments': '{"user_question":"我今天身體狀況如何？"}', 'name': 'draw_tarot_cards'}, 'type': 'function'}]}]
    # c=[{'role': 'system', 'content': ''}, {'role': 'user', 'content': ''}, {'content': None, 'refusal': None, 'role': 'assistant', 'annotations': [], 'audio': None, 'function_call': None, 'tool_calls': [{'id': 'call_hXgDiiRnxDUWDpqMbR7FB0Dn', 'function': {'arguments': '{"user_question":"我今天身體狀況如何？"}', 'name': 'draw_tarot_cards'}, 'type': 'function'}]}]
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        match function_name:

            case "check_scam_phone":
                phone_number = function_args.get("phone_number")
                function_response = await perform_scam_phone_check(
                    phone_number,
                    INTERNAL_BLACKLIST_SET 
                )
                print("function_response: ", function_response)
                if function_response is None:
                    function_response = []
                messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response
                })
                print("messages: ", messages)

            case "draw_tarot_cards":
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
                reply_text=[]
                reply_text.append(
                    "占卜問題: "+user_question+"\n占卜結果: " 
                    + "\n            " + cardList[0] + "\n" + cardList[4] + "          " + cardList[5] 
                    + "\n            " + cardList[6] + "\n" + cardList[2] + "          " + cardList[1] 
                    + "\n            " + cardList[3] + "\n\n全局暗示: "+ cardList[7]
                )
                messages = [msg for msg in messages if msg['role'] != 'system']
                print("messages: ", messages)
                messages = [{"role": "user", "content": tarotToAIsystemPrompt}]

                # messages.append({
                #         "tool_call_id": tool_call.id,
                #         "role": "tool",
                #         "name": function_name,
                #         "content": ""
                # })
                print("messages: ", messages)
                second_response = await openai_client.chat.completions.create(
                    model="gpt-4.1-2025-04-14",
                    messages=messages,
                    temperature=1.2,
                    presence_penalty=0.5,
                    frequency_penalty=0.1,
                    top_p=0.9,
                    max_tokens=2000,
                    n=1
                )
                print("second_response: ", second_response)

                reply_text.append(second_response.choices[0].message.content.strip()) 
                if isinstance(reply_text, list):
                    print_reply_text = ", ".join(reply_text)
                print("\nOutput: "+print_reply_text)
                return reply_text
                
    final_response = await openai_client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=messages,
        temperature=1.2,
        presence_penalty=0.5,
        frequency_penalty=0.1,
        top_p=0.9,
        max_tokens=2000,
        n=1
    )
    print("final_response: ", final_response)
    reply_text=[]
    if response.choices[0].message.content:
        reply_text.append(response.choices[0].message.content.strip())
    reply_text.append(final_response.choices[0].message.content.strip())
    return reply_text
   
    #四元素 選擇牌陣
    #給GPT清晰的文字，過去牌：杖2
    #下一段對話給予主人勇氣
    #量化結論 出數字 或是 評價評分
    #貼圖每次重新歸納圖片重點，保持靈活性
    #用拉岡理論去開導人