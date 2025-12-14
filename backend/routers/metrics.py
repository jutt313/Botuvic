"""Metrics router"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from database import get_supabase_admin_client
from typing import List, Dict, Any

router = APIRouter(prefix="/api/metrics", tags=["metrics"])
security = HTTPBearer()

@router.get("/")
async def get_metrics(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user metrics"""
    try:
        # Get user from token
        from supabase import create_client
        from config import settings
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        
        user_response = supabase.auth.get_user(credentials.credentials)
        
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = user_response.user.id
        admin_client = get_supabase_admin_client()
        
        # Get project count
        projects = admin_client.table("projects").select("id").eq("user_id", user_id).execute()
        total_projects = len(projects.data) if projects.data else 0
        
        # TODO: Calculate actual metrics from usage_tracking table
        # For now, return mock data
        return {
            "totalProjects": total_projects,
            "tasksCompleted": 324,
            "aiCalls": 1247,
            "errorsFixed": 89
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")

@router.get("/activity")
async def get_activity(
    range: str = "week",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get activity data for charts"""
    try:
        # Get user from token
        from supabase import create_client
        from config import settings
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        
        user_response = supabase.auth.get_user(credentials.credentials)
        
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # TODO: Fetch actual activity data from usage_tracking
        # For now, return mock data
        if range == "week":
            return [
                {"date": "Mon", "commits": 12, "tasks": 8, "aiCalls": 45},
                {"date": "Tue", "commits": 15, "tasks": 12, "aiCalls": 67},
                {"date": "Wed", "commits": 8, "tasks": 6, "aiCalls": 34},
                {"date": "Thu", "commits": 20, "tasks": 15, "aiCalls": 89},
                {"date": "Fri", "commits": 18, "tasks": 10, "aiCalls": 56},
                {"date": "Sat", "commits": 5, "tasks": 3, "aiCalls": 23},
                {"date": "Sun", "commits": 7, "tasks": 5, "aiCalls": 28}
            ]
        else:
            # Month data
            return [
                {"date": "Week 1", "commits": 45, "tasks": 32, "aiCalls": 180},
                {"date": "Week 2", "commits": 52, "tasks": 38, "aiCalls": 210},
                {"date": "Week 3", "commits": 38, "tasks": 28, "aiCalls": 165},
                {"date": "Week 4", "commits": 61, "tasks": 45, "aiCalls": 245}
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch activity: {str(e)}")

