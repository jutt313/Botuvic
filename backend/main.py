from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os
import logging

# Setup comprehensive logging FIRST
from utils.logger import setup_logging, get_logger
setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

logger.info("=" * 80)
logger.info("BOTUVIC Backend - Starting Application")
logger.info("=" * 80)

from routers import auth_router
from routers import projects
from routers import metrics
from routers import conversations
from middleware.logging_middleware import LoggingMiddleware

load_dotenv()

app = FastAPI(title="BOTUVIC API", version="1.0.0", redirect_slashes=False)

# Add logging middleware FIRST (before other middleware)
app.add_middleware(LoggingMiddleware)

# CORS middleware
logger.info("STEP: Configuring CORS middleware")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8765"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("STEP: CORS middleware configured")

# Direct metrics endpoints to prevent 307 redirects
security = HTTPBearer()

async def _get_user_metrics(credentials: HTTPAuthorizationCredentials):
    """Get metrics for authenticated user"""
    from supabase import create_client
    from config import settings
    from database import get_supabase_admin_client
    from fastapi import HTTPException

    supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
    user_response = supabase.auth.get_user(credentials.credentials)

    if not user_response.user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = user_response.user.id
    admin_client = get_supabase_admin_client()

    projects_result = admin_client.table("projects").select("id").eq("user_id", user_id).execute()
    total_projects = len(projects_result.data) if projects_result.data else 0

    return {
        "totalProjects": total_projects,
        "tasksCompleted": 324,
        "aiCalls": 1247,
        "errorsFixed": 89
    }

@app.get("/api/metrics")
async def get_metrics(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user metrics - no trailing slash"""
    return await _get_user_metrics(credentials)

# Include routers with logging
logger.info("STEP: Registering API routers")
app.include_router(auth_router)
logger.info("STEP: Auth router registered")
app.include_router(projects.router)
logger.info("STEP: Projects router registered")
app.include_router(metrics.router)
logger.info("STEP: Metrics router registered")
app.include_router(conversations.router)
logger.info("STEP: Conversations router registered")
logger.info("STEP: All routers registered successfully")

@app.get("/")
async def root():
    """Root endpoint - API status"""
    logger.info("STEP: Root endpoint accessed")
    return {"message": "BOTUVIC API is running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    logger.info("STEP: Health check endpoint accessed")
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    logger.info("")
    logger.info("=" * 80)
    logger.info("🚀 BOTUVIC Backend - Starting Uvicorn Server")
    logger.info("=" * 80)
    logger.info("   Host: 0.0.0.0")
    logger.info("   Port: 8000")
    logger.info("   Logging: ENABLED (Full Transparency)")
    logger.info("   Request Tracking: ACTIVE")
    logger.info("=" * 80)
    logger.info("")
    logger.info("📡 Server is ready! All requests will be logged below:")
    logger.info("")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)  # We handle logging ourselves

