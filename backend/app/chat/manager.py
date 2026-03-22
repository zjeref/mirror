import logging

from fastapi import WebSocket

logger = logging.getLogger("mirror.ws")


class ConnectionManager:
    """Manages WebSocket connections per user with dead connection cleanup."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                ws for ws in self.active_connections[user_id] if ws != websocket
            ]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            dead = []
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            # Clean up dead connections
            for ws in dead:
                self.disconnect(ws, user_id)

    async def send_to_connection(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception:
            logger.warning("Failed to send to WebSocket — connection may be dead")


manager = ConnectionManager()
