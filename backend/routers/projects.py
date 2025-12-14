"""Projects router"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from database import get_supabase_admin_client
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["projects"])
security = HTTPBearer()

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str = None
    status: str = None
    created_at: str = None

@router.get("/", response_model=List[ProjectResponse])
async def get_user_projects(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all projects for the authenticated user"""
    try:
        # Get user from token
        admin_client = get_supabase_admin_client()
        
        # Verify token and get user
        from supabase import create_client
        from config import settings
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        
        user_response = supabase.auth.get_user(credentials.credentials)
        
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = user_response.user.id
        
        # Get projects for user
        projects = admin_client.table("projects").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        if not projects.data:
            return []
        
        return [
            ProjectResponse(
                id=str(proj.get("id", "")),
                name=proj.get("name", "Unnamed Project"),
                description=proj.get("description"),
                status=proj.get("status"),
                created_at=str(proj.get("created_at", ""))
            )
            for proj in projects.data
        ]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Failed to fetch projects: {str(e)}")

