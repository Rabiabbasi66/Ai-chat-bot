from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings
from typing import Optional
import logging

# Setup logging for cleaner output than 'print'
logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

database = Database()

async def connect_to_mongodb():
    """Connect to MongoDB Atlas and initialize indexes"""
    try:
        # 1. Initialize the client
        database.client = AsyncIOMotorClient(settings.mongodb_uri)
        database.db = database.client[settings.mongodb_db_name]
        
        # 2. Test connection (Ping)
        await database.client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas")
        
        # 3. Setup Indexes
        if database.db is not None:
            try:
                # Unique index for emails is critical for your registration logic
                await database.db.users.create_index("email", unique=True)
                
                # Performance indexes for chat
                await database.db.messages.create_index([("chat_id", 1), ("created_at", -1)])
                await database.db.chat_sessions.create_index("user_id")
                
                print("🚀 Database indexes initialized")
            except Exception as index_error:
                # Don't crash the server if index creation fails (e.g., index already exists)
                print(f"⚠️ Index initialization warning: {index_error}")
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise

async def close_mongodb_connection():
    """Close MongoDB connection"""
    if database.client:
        database.client.close()
        print("🔌 MongoDB connection closed")

def get_collection(collection_name: str):
    """Get specific collection with a safety check"""
    if database.db is None:
        raise ConnectionError("Database not initialized. Ensure connect_to_mongodb() is called on startup.")
    return database.db[collection_name]