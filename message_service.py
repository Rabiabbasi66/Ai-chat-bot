from datetime import datetime, timezone
from typing import List, Optional, Dict
from bson import ObjectId  # Added this import
from ..database import get_collection

class MessageService:
    def __init__(self):
        pass

    @property
    def messages_collection(self):
        return get_collection("messages")

    @property
    def chat_sessions_collection(self):
        return get_collection("chat_sessions")
    
    async def create_message(
        self,
        chat_id: str,
        user_id: str,
        content: str,
        sender_type: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Create a new message and link it to the chat session"""
        message = {
            "chat_id": chat_id,
            "user_id": user_id,
            "content": content,
            "sender_type": sender_type,
            "created_at": datetime.now(timezone.utc), # Updated to modern UTC
            "is_read": False,
            "metadata": metadata or {}
        }
        
        result = await self.messages_collection.insert_one(message)
        message["id"] = str(result.inserted_id)
        
        # FIX: Convert string chat_id to ObjectId for the session update
        try:
            session_id = ObjectId(chat_id)
            await self.chat_sessions_collection.update_one(
                {"_id": session_id},
                {
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                    "$inc": {"message_count": 1}
                },
                upsert=False # Changed to False to prevent creating empty sessions
            )
        except Exception as e:
            print(f"Error updating session: {e}")
        
        return message
    
    async def get_messages(
        self,
        chat_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict]:
        """Get messages for a chat session"""
        messages = await self.messages_collection.find(
            {"chat_id": chat_id}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        
        for msg in messages:
            msg["id"] = str(msg["_id"])
            del msg["_id"]
        
        return messages[::-1]
    
    async def create_chat_session(self, user_id: str, title: str = "New Chat") -> Dict:
        """Create a new chat session"""
        session = {
            "user_id": user_id,
            "title": title,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "message_count": 0,
            "is_active": True
        }
        
        result = await self.chat_sessions_collection.insert_one(session)
        session["id"] = str(result.inserted_id)
        
        return session

    # ... remaining methods remain the same ...

message_service = MessageService()