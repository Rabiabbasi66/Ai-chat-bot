from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class UserBase(BaseModel):
    email: str
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[dict] = {}

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_verified: bool = False
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class MessageBase(BaseModel):
    content: str
    sender_type: str  # "user" or "ai"

class MessageCreate(MessageBase):
    chat_id: str
    user_id: str

class Message(MessageBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    chat_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = False
    metadata: Optional[dict] = {}
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class ChatSession(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    title: Optional[str] = "New Chat"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    is_active: bool = True
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class AIConfig(BaseModel):
    personality: str = "helpful"
    tone: str = "friendly"
    response_length: str = "medium"
    language: str = "en"
    expertise_areas: List[str] = []

class ChatSettings(BaseModel):
    theme: str = "light"
    font_size: str = "medium"
    notifications: bool = True
    sound_enabled: bool = True
    ai_config: AIConfig = AIConfig()