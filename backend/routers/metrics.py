"""Metrics router"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from database import get_supabase_admin_client
from typing import List, Dict, Any
from utils.logger import get_logger, log_step, log_error_with_context

logger = get_logger(__name__)

router = APIRouter(prefix="/api/metrics", tags=["metrics"])
security = HTTPBearer()

@router.get("/activity")
async def get_activity(
    range: str = "week",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get activity data for charts"""
    log_step(logger, "Get activity request started", {"range": range})
    
    try:
        log_step(logger, "Validating user token")
        # Get user from token
        from supabase import create_client
        from config import settings
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        
        user_response = supabase.auth.get_user(credentials.credentials)
        
        if not user_response.user:
            log_error_with_context(logger, Exception("Not authenticated"), {
                "endpoint": "/metrics/activity",
                "error_type": "AuthenticationError"
            })
            raise HTTPException(status_code=401, detail="Not authenticated")

        log_step(logger, "Token validated", {"user_id": user_response.user.id})
        log_step(logger, "Fetching activity data", {"range": range})
        
        # TODO: Fetch actual activity data from usage_tracking
        # For now, return mock data
        if range == "week":
            log_step(logger, "Returning weekly activity data")
            logger.info(f"STEP: Get activity complete - weekly data")
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
            log_step(logger, "Returning monthly activity data")
            logger.info(f"STEP: Get activity complete - monthly data")
            return [
                {"date": "Week 1", "commits": 45, "tasks": 32, "aiCalls": 180},
                {"date": "Week 2", "commits": 52, "tasks": 38, "aiCalls": 210},
                {"date": "Week 3", "commits": 38, "tasks": 28, "aiCalls": 165},
                {"date": "Week 4", "commits": 61, "tasks": 45, "aiCalls": 245}
            ]
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/metrics/activity",
            "range": range,
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=f"Failed to fetch activity: {str(e)}")

