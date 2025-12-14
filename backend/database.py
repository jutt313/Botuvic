from supabase import create_client, Client
from config import settings

def get_supabase_client() -> Client:
    """Get Supabase client for authenticated requests"""
    return create_client(settings.supabase_url, settings.supabase_anon_key)

def get_supabase_admin_client() -> Client:
    """Get Supabase admin client for service role operations"""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

