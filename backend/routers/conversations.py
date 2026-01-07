"""Conversation history router"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from database import get_supabase_admin_client
from typing import List
from pydantic import BaseModel
from utils.logger import get_logger, log_step, log_error_with_context

logger = get_logger(__name__)

router = APIRouter(prefix="/api/projects", tags=["conversations"])
security = HTTPBearer()

class MessageCreate(BaseModel):
    role: str  # 'user' or 'assistant'
    message: str

class MessageResponse(BaseModel):
    id: str
    project_id: str
    role: str
    message: str
    created_at: str

@router.post("/{project_id}/messages", response_model=MessageResponse)
async def save_message(
    project_id: str,
    message_data: MessageCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Save a conversation message"""
    log_step(logger, "Save message request started", {"project_id": project_id, "role": message_data.role})
    
    try:
        log_step(logger, "Getting Supabase admin client")
        admin_client = get_supabase_admin_client()

        log_step(logger, "Validating user token")
        from supabase import create_client
        from config import settings
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)

        user_response = supabase.auth.get_user(credentials.credentials)

        if not user_response.user:
            log_error_with_context(logger, Exception("Not authenticated"), {
                "endpoint": "/messages",
                "project_id": project_id,
                "error_type": "AuthenticationError"
            })
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_id = user_response.user.id
        log_step(logger, "Token validated", {"user_id": user_id})

        log_step(logger, "Verifying project ownership", {"project_id": project_id})
        # Verify project belongs to user
        project = admin_client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()

        if not project.data:
            log_error_with_context(logger, Exception("Project not found"), {
                "endpoint": "/messages",
                "project_id": project_id,
                "user_id": user_id,
                "error_type": "NotFoundError"
            })
            raise HTTPException(status_code=404, detail="Project not found")

        log_step(logger, "Saving message to database", {"project_id": project_id, "role": message_data.role})
        # Save message
        result = admin_client.table("conversation_history").insert({
            "project_id": project_id,
            "user_id": user_id,
            "role": message_data.role,
            "message": message_data.message
        }).execute()

        if not result.data:
            log_error_with_context(logger, Exception("Failed to save message"), {
                "endpoint": "/messages",
                "project_id": project_id,
                "error_type": "DatabaseError"
            })
            raise HTTPException(status_code=500, detail="Failed to save message")

        msg = result.data[0]
        log_step(logger, "Message saved successfully", {"message_id": msg.get("id"), "project_id": project_id})
        
        logger.info(f"STEP: Save message complete")
        return MessageResponse(
            id=str(msg.get("id")),
            project_id=str(msg.get("project_id")),
            role=msg.get("role"),
            message=msg.get("message"),
            created_at=str(msg.get("created_at"))
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/messages",
            "project_id": project_id,
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=f"Failed to save message: {str(e)}")

@router.get("/{project_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    project_id: str,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get conversation history for a project"""
    log_step(logger, "Get messages request started", {"project_id": project_id, "limit": limit})
    
    try:
        log_step(logger, "Getting Supabase admin client")
        admin_client = get_supabase_admin_client()

        log_step(logger, "Validating user token")
        from supabase import create_client
        from config import settings
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)

        user_response = supabase.auth.get_user(credentials.credentials)

        if not user_response.user:
            log_error_with_context(logger, Exception("Not authenticated"), {
                "endpoint": "/messages",
                "project_id": project_id,
                "error_type": "AuthenticationError"
            })
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_id = user_response.user.id
        log_step(logger, "Token validated", {"user_id": user_id})

        log_step(logger, "Verifying project ownership", {"project_id": project_id})
        # Verify project belongs to user
        project = admin_client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()

        if not project.data:
            log_error_with_context(logger, Exception("Project not found"), {
                "endpoint": "/messages",
                "project_id": project_id,
                "user_id": user_id,
                "error_type": "NotFoundError"
            })
            raise HTTPException(status_code=404, detail="Project not found")

        log_step(logger, "Fetching messages from database", {"project_id": project_id, "limit": limit})
        # Get messages
        messages = admin_client.table("conversation_history").select("*").eq("project_id", project_id).order("created_at", desc=False).limit(limit).execute()

        if not messages.data:
            log_step(logger, "No messages found", {"project_id": project_id})
            return []

        message_count = len(messages.data)
        log_step(logger, "Messages retrieved", {"count": message_count, "project_id": project_id})
        
        logger.info(f"STEP: Get messages complete - {message_count} messages")
        return [
            MessageResponse(
                id=str(msg.get("id")),
                project_id=str(msg.get("project_id")),
                role=msg.get("role"),
                message=msg.get("message"),
                created_at=str(msg.get("created_at"))
            )
            for msg in messages.data
        ]
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/messages",
            "project_id": project_id,
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")

@router.delete("/{project_id}/messages")
async def clear_messages(
    project_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Clear conversation history for a project"""
    log_step(logger, "Clear messages request started", {"project_id": project_id})
    
    try:
        log_step(logger, "Getting Supabase admin client")
        admin_client = get_supabase_admin_client()

        log_step(logger, "Validating user token")
        from supabase import create_client
        from config import settings
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)

        user_response = supabase.auth.get_user(credentials.credentials)

        if not user_response.user:
            log_error_with_context(logger, Exception("Not authenticated"), {
                "endpoint": "/messages/clear",
                "project_id": project_id,
                "error_type": "AuthenticationError"
            })
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_id = user_response.user.id
        log_step(logger, "Token validated", {"user_id": user_id})

        log_step(logger, "Verifying project ownership", {"project_id": project_id})
        # Verify project belongs to user
        project = admin_client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()

        if not project.data:
            log_error_with_context(logger, Exception("Project not found"), {
                "endpoint": "/messages/clear",
                "project_id": project_id,
                "user_id": user_id,
                "error_type": "NotFoundError"
            })
            raise HTTPException(status_code=404, detail="Project not found")

        log_step(logger, "Deleting messages from database", {"project_id": project_id})
        # Delete messages
        admin_client.table("conversation_history").delete().eq("project_id", project_id).execute()

        log_step(logger, "Messages cleared successfully", {"project_id": project_id})
        logger.info(f"STEP: Clear messages complete")
        return {"message": "Conversation history cleared"}
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/messages/clear",
            "project_id": project_id,
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=f"Failed to clear messages: {str(e)}")
