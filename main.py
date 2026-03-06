from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import uvicorn

from .config import settings
from .database import connect_to_mongodb, close_mongodb_connection
from .routes import websocket, chat, user 

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongodb()
    yield
    await close_mongodb_connection()

app = FastAPI(
    title="AI Chat Application",
    lifespan=lifespan,
    docs_url=None, 
    redoc_url=None
)

# --- CORS CONFIGURATION ---
# We use a broad setup here to ensure your local testing isn't blocked
# In main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"], # Add both versions
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router includes - MUST stay after CORSMiddleware
app.include_router(websocket.router)
app.include_router(chat.router)
app.include_router(user.router)

@app.get("/")
async def root():
    return {"message": "Welcome to AI Chat API"}

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def custom_redoc_ui_html():
    return get_redoc_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "ai_service": "configured" if settings.openai_api_key else "not_configured"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )