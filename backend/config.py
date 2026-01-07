from pydantic_settings import BaseSettings
from typing import Optional
from utils.logger import get_logger, log_step

logger = get_logger(__name__)

class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env

log_step(logger, "Loading configuration from .env")
try:
settings = Settings()
    log_step(logger, "Configuration loaded successfully", {
        "supabase_url": settings.supabase_url[:30] + "..." if len(settings.supabase_url) > 30 else settings.supabase_url
    })
except Exception as e:
    logger.error(f"ERROR: Failed to load configuration: {str(e)}", exc_info=True)
    raise

