from supabase import create_client, Client
from config import settings
from utils.logger import get_logger, log_step

logger = get_logger(__name__)

def get_supabase_client() -> Client:
    """Get Supabase client for authenticated requests"""
    log_step(logger, "Creating Supabase client", {"type": "authenticated"})
    try:
        client = create_client(settings.supabase_url, settings.supabase_anon_key)
        logger.info(f"STEP: Supabase client created successfully")
        return client
    except Exception as e:
        logger.error(f"ERROR: Failed to create Supabase client: {str(e)}", exc_info=True)
        raise

def get_supabase_admin_client() -> Client:
    """Get Supabase admin client for service role operations"""
    log_step(logger, "Creating Supabase admin client", {"type": "service_role"})
    try:
        client = create_client(settings.supabase_url, settings.supabase_service_role_key)
        logger.info(f"STEP: Supabase admin client created successfully")
        return client
    except Exception as e:
        logger.error(f"ERROR: Failed to create Supabase admin client: {str(e)}", exc_info=True)
        raise

