from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
import json
from datetime import datetime, timezone
from ..services.ai_service import ai_service
from ..services.message_service import message_service

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[Dict[str, Any]]] = {}
        self.user_connections: Dict[str, str] = {} 
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        connection_id = f"{user_id}_{datetime.now(timezone.utc).timestamp()}"
        self.user_connections[connection_id] = user_id
        
        self.active_connections[user_id].append({
            "websocket": websocket,
            "connection_id": connection_id
        })
        return connection_id
    
    def disconnect(self, connection_id: str):
        user_id = self.user_connections.get(connection_id)
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id] = [
                conn for conn in self.active_connections[user_id]
                if conn["connection_id"] != connection_id
            ]
        if connection_id in self.user_connections:
            del self.user_connections[connection_id]

    async def send_personal_message(self, message: dict, user_id: str):
        """Fixed: Sends a flattened message to match frontend expectations"""
        if user_id in self.active_connections:
            for conn in self.active_connections[user_id]:
                try:
                    # Flatten the 'data' key so frontend can read data.content directly
                    msg_type = message.get("type")
                    payload = message.get("data", {})
                    payload["type"] = msg_type 
                    
                    cleaned_message = self._serialize_datetime(payload)
                    await conn["websocket"].send_json(cleaned_message)
                except Exception:
                    pass

    def _serialize_datetime(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: self._serialize_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(i) for i in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj

manager = ConnectionManager()

# Ensure this matches the frontend call seen in terminal: /ws/chat/user_...
@router.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    connection_id = await manager.connect(websocket, user_id)
    
    # Initial status message
    await manager.send_personal_message({
        "type": "connected",
        "data": {"message": "Welcome to AI Chat!"}
    }, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")
                
                if message_type == "message":
                    content = message_data.get("content", "")
                    chat_id = message_data.get("chat_id", "")
                    personality = message_data.get("personality", "helpful")
                    
                    if not content or not chat_id:
                        continue
                    
                    # 1. Save and Broadcast User Message
                    user_message = await message_service.create_message(
                        chat_id=chat_id, user_id=user_id, content=content, sender_type="user"
                    )
                    
                    await manager.send_personal_message({
                        "type": "message",
                        "data": {
                            "message_id": str(user_message["id"]),
                            "content": content,
                            "sender_type": "user",
                            "chat_id": chat_id,
                            "timestamp": user_message["created_at"]
                        }
                    }, user_id)
                    
                    # 2. Typing Indicator (Match frontend: handleTypingIndicator checks .is_typing)
                    await manager.send_personal_message({
                        "type": "typing",
                        "data": {"is_typing": True, "sender": "ai", "chat_id": chat_id}
                    }, user_id)
                    
                    # 3. AI Logic
                    messages = await message_service.get_messages(chat_id, limit=10)
                    history = [
                        {"role": "user" if m["sender_type"] == "user" else "assistant", "content": m["content"]}
                        for m in messages
                    ]
                    
                    ai_response = await ai_service.generate_response(
                        message=content, conversation_history=history, personality=personality
                    )
                    
                    # 4. Stop Typing
                    await manager.send_personal_message({
                        "type": "typing",
                        "data": {"is_typing": False, "sender": "ai", "chat_id": chat_id}
                    }, user_id)
                    
                    if ai_response["success"]:
                        ai_msg = await message_service.create_message(
                            chat_id=chat_id, user_id=user_id, content=ai_response["content"],
                            sender_type="ai"
                        )
                        
                        await manager.send_personal_message({
                            "type": "message",
                            "data": {
                                "message_id": str(ai_msg["id"]),
                                "content": ai_response["content"],
                                "sender_type": "ai",
                                "chat_id": chat_id,
                                "timestamp": ai_msg["created_at"]
                            }
                        }, user_id)

            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)