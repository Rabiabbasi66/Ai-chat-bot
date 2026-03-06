from fastapi import APIRouter, HTTPException, status, Body # Added Body
from typing import Optional
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from ..schemas import UserCreate, UserResponse, Token
from ..database import get_collection
from passlib.context import CryptContext
from jose import jwt
from ..config import settings
from pydantic import BaseModel, EmailStr # Added for Login request

router = APIRouter(prefix="/api/users", tags=["users"])

# --- FIX 1: Set argon2 as the primary scheme ---
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Helper for login request body
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    users_collection = get_collection("users")
    
    # Check if user exists
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = user.model_dump() if hasattr(user, "model_dump") else user.dict()
    
    # --- Argon2 will now handle any password length ---
    user_dict["password"] = pwd_context.hash(user_dict["password"])
    user_dict["created_at"] = datetime.now(timezone.utc)
    user_dict["is_active"] = True
    user_dict["is_verified"] = False
    user_dict["avatar_url"] = user_dict.get("avatar_url", None)

    result = await users_collection.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    
    return user_dict

# --- FIX 2: Fixed login to accept JSON body instead of query params ---
@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest):
    users_collection = get_collection("users")
    
    user = await users_collection.find_one({"email": credentials.email})
    
    # Verify using Argon2
    if not user or not pwd_context.verify(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}