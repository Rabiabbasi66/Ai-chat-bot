from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Generic, TypeVar
from datetime import datetime

# Define a TypeVar for Generic WebSocket messages
T = TypeVar("T")

# Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    
    
    # Add this to your schemas.py
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

# User
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    is_active: bool

# Message
class MessageResponse(BaseModel):
    id: str
    content: str
    sender_type: str
    chat_id: str
    user_id: str
    created_at: datetime
    is_read: bool

# Chat
class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int

# WebSocket Messages (Using Generics to fix the 'data' override error)
class WSMessage(BaseModel, Generic[T]):
    type: str  # "message", "typing", "status", "error"
    data: T
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    
    class ChatSettings(BaseModel):
        personality: str = "helpful"
        ai_model: Optional[str] = "gpt-3.5-turbo"
        temperature: float = 0.7

class WSChatMessage(WSMessage):
    class Data(BaseModel):
        content: str
        sender_type: str
        chat_id: str
        message_id: str
    
    type: str = "message"
    data: Data # This now works because WSMessage is Generic

class WSTyping(WSMessage):
    class Data(BaseModel):
        chat_id: str
        is_typing: bool
        user_id: str
    
    type: str = "typing"
    data: Data