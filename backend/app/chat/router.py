from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.auth.service import verify_access_token
from app.chat.engine import ConversationEngine
from app.chat.manager import manager
from app.chat.schemas import ConversationResponse, MessageResponse
from app.dependencies import get_current_user, get_db
from app.models.conversation import Conversation, Message
from app.models.user import User

router = APIRouter()


@router.websocket("/ws")
async def chat_websocket(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for real-time chat."""
    # Authenticate via token query param
    user_id = verify_access_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=4001, reason="User not found")
        return

    await manager.connect(websocket, user_id)
    engine = ConversationEngine(db, user)

    try:
        # Send welcome message
        await manager.send_to_connection(
            websocket,
            {
                "type": "message",
                "content": f"Hey {user.name}. How are you doing right now?",
                "sender": "mirror",
            },
        )

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await manager.send_to_connection(websocket, {"type": "pong"})
                continue

            if msg_type == "message":
                content = data.get("content", "").strip()
                if not content:
                    continue

                conversation_id = data.get("conversation_id")
                response = await engine.handle_message(content, conversation_id)
                await manager.send_to_connection(websocket, response)

            elif msg_type == "flow_response":
                # Phase 2: handle structured flow responses
                await manager.send_to_connection(
                    websocket,
                    {
                        "type": "message",
                        "content": "Flows will be available soon. For now, just talk to me freely.",
                        "sender": "mirror",
                    },
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    limit: int = Query(default=20, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's conversations."""
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [
        ConversationResponse(
            id=c.id,
            title=c.title,
            conversation_type=c.conversation_type,
            is_active=c.is_active,
            created_at=c.created_at,
            message_count=c.messages.count(),
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(
    conversation_id: str,
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get messages for a conversation."""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    messages.reverse()  # Return in chronological order

    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            message_type=m.message_type,
            created_at=m.created_at,
            metadata=m.metadata_,
        )
        for m in messages
    ]
