from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from app.auth.service import verify_access_token
from app.chat.engine import ConversationEngine
from app.chat.flows.base import UserContext
from app.chat.manager import manager
from app.chat.schemas import ConversationResponse, MessageResponse
from app.dependencies import get_current_user
from app.models.conversation import Conversation, Message
from app.models.user import User

router = APIRouter()


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket, token: str = Query(...)):
    user_id = verify_access_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user = await User.get(user_id)
    if not user:
        await websocket.close(code=4001, reason="User not found")
        return

    await manager.connect(websocket, str(user.id))
    engine = ConversationEngine(user)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await manager.send_to_connection(websocket, {"type": "pong"})
                continue

            if msg_type == "session_start":
                context = UserContext(user_id=str(user.id), user_name=user.name)
                greeting = await engine.session_engine.handle_session_start(context)
                if greeting:
                    await manager.send_to_connection(websocket, greeting)
                continue

            if msg_type == "message":
                content = data.get("content", "").strip()
                if not content:
                    continue
                conversation_id = data.get("conversation_id")
                response = await engine.handle_message(content, conversation_id)
                await manager.send_to_connection(websocket, response)

    except WebSocketDisconnect:
        manager.disconnect(websocket, str(user.id))


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    limit: int = Query(default=20, le=100),
    user: User = Depends(get_current_user),
):
    conversations = await Conversation.find(
        Conversation.user_id == str(user.id)
    ).sort("-updated_at").limit(limit).to_list()

    results = []
    for c in conversations:
        msg_count = await Message.find(Message.conversation_id == str(c.id)).count()
        results.append(ConversationResponse(
            id=str(c.id),
            title=c.title,
            conversation_type=c.conversation_type,
            is_active=c.is_active,
            created_at=c.created_at,
            message_count=msg_count,
        ))
    return results


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_user),
):
    conversation = await Conversation.get(conversation_id)
    if not conversation or conversation.user_id != str(user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = await Message.find(
        Message.conversation_id == conversation_id
    ).sort("-created_at").limit(limit).to_list()
    messages.reverse()

    return [
        MessageResponse(
            id=str(m.id),
            role=m.role,
            content=m.content,
            message_type=m.message_type,
            created_at=m.created_at,
            metadata=m.metadata_,
        )
        for m in messages
    ]
