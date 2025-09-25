import uuid
from supabase import AsyncClient
from postgrest.exceptions import APIError

async def upsert_user(db_client: AsyncClient, user_id: str, user_name: str):
    """新增或更新使用者資訊"""
    await db_client.table("users").upsert({
        "userid": user_id,
        "username": user_name if user_name else "",
        "lastactiveat": "NOW()"
    }, returning="minimal").execute()

async def save_group_message(db_client: AsyncClient, group_id: str, group_name: str, user_id: str, content: str):
    """儲存群組訊息"""
    # 更新群組資訊
    await db_client.table("groups").upsert({
        "groupid": group_id, "groupname": group_name, "updatedat": "NOW()"
    }, returning="minimal").execute()
    
    # 更新會話資訊
    await db_client.table("sessions").upsert({
        "sessionid": group_id, "groupid": group_id, "sessiontype": "group", "updatedat": "NOW()"
    }, returning="minimal").execute()
    
    # 儲存使用者傳入的訊息
    await db_client.table("messages").insert({
        "messageid": str(uuid.uuid4()), "sessionid": group_id, "userid": user_id,
        "content": content, "direction": "inbound"
    }, returning="minimal").execute()

async def manage_user_session_and_message(db_client: AsyncClient, user_id: str, content: str):
    """管理一對一聊天的工作流程：檢查/建立 session 並儲存訊息"""
    session_query = await db_client.table("sessions").select("sessionid, status").eq("userid", user_id).order("createdat", desc=True).limit(1).execute()
    
    session_id = None
    if not session_query.data or session_query.data[0]["status"] == "ended":
        session_id = str(uuid.uuid4())
        await db_client.table("sessions").insert({
            "sessionid": session_id, "userid": user_id, "status": "active"
        }, returning="minimal").execute()
    else:
        session_id = session_query.data[0]["sessionid"]
        await db_client.table("sessions").update({"updatedat": "NOW()"}).eq("sessionid", session_id).execute()

    await db_client.table("messages").insert({
        "messageid": str(uuid.uuid4()), "sessionid": session_id, "userid": user_id,
        "content": content, "direction": "inbound"
    }, returning="minimal").execute()
    
    return session_id

async def save_ai_reply(db_client: AsyncClient, session_id: str, user_id: str, content: str):#儲存的不同模式
    """儲存 AI 的回覆訊息"""
    try:
        await db_client.table("messages").insert({
            "messageid": str(uuid.uuid4()), "sessionid": session_id, "userid": user_id,
            "content": content, "direction": "outbound"
        }, returning="minimal").execute()
    except APIError as e:
        print(f"❌ Error inserting AI message into Messages table: {e}")

async def get_conversation_history(db_client: AsyncClient, session_id: str, limit: int = 20):
    """獲取指定 session 的對話歷史"""
    messages_query = await db_client.table("messages").select("*").eq("sessionid", session_id).order("createdat", desc=True).limit(limit).execute()
    
    user_ids = {msg["userid"] for msg in messages_query.data}
    users_query = await db_client.table("users").select("userid, username").in_("userid", list(user_ids)).execute()
    user_names_map = {user["userid"]: user["username"] for user in users_query.data}
    
    history = "\n\n".join([
        f"{user_names_map.get(msg['userid'], '不知名主人')}: {msg['content']}" if msg["direction"] == "inbound" else f"吃吃: {msg['content']}"
        for msg in reversed(messages_query.data)
    ])
    return history