"""Projects router"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from database import get_supabase_admin_client
from typing import List
from pydantic import BaseModel
from utils.logger import get_logger, log_step, log_error_with_context

logger = get_logger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])
security = HTTPBearer()

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str = None
    status: str = None
    path: str = None
    created_at: str = None

class ProjectCreate(BaseModel):
    name: str
    path: str
    description: str = None
    status: str = "new"  # "new" or "in_progress"

@router.get("/", response_model=List[ProjectResponse])
async def get_user_projects(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all projects for the authenticated user"""
    log_step(logger, "Get user projects request started")
    
    try:
        log_step(logger, "Getting Supabase admin client")
        admin_client = get_supabase_admin_client()
        
        log_step(logger, "Validating user token")
        # Verify token and get user
        from supabase import create_client
        from config import settings
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        
        user_response = supabase.auth.get_user(credentials.credentials)
        
        if not user_response.user:
            log_error_with_context(logger, Exception("Not authenticated"), {
                "endpoint": "/projects",
                "error_type": "AuthenticationError"
            })
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = user_response.user.id
        log_step(logger, "Token validated", {"user_id": user_id})
        
        log_step(logger, "Fetching projects from database", {"user_id": user_id})
        # Get projects for user
        projects = admin_client.table("projects").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        if not projects.data:
            log_step(logger, "No projects found", {"user_id": user_id})
            return []
        
        project_count = len(projects.data)
        log_step(logger, "Projects retrieved", {"count": project_count, "user_id": user_id})
        
        logger.info(f"STEP: Get user projects complete - {project_count} projects")
        return [
            ProjectResponse(
                id=str(proj.get("id", "")),
                name=proj.get("name", "Unnamed Project"),
                description=proj.get("description"),
                status=proj.get("status", "new"),
                path=proj.get("path"),
                created_at=str(proj.get("created_at", ""))
            )
            for proj in projects.data
        ]
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/projects",
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=401, detail=f"Failed to fetch projects: {str(e)}")

@router.get("/by-path", response_model=ProjectResponse)
async def get_project_by_path(
    path: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Check if a path is registered as a project"""
    log_step(logger, "Get project by path request started", {"path": path})
    
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
                "endpoint": "/projects/by-path",
                "path": path,
                "error_type": "AuthenticationError"
            })
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_id = user_response.user.id
        log_step(logger, "Token validated", {"user_id": user_id})

        log_step(logger, "Searching for project by path", {"path": path})
        # Check if project exists with this path
        projects = admin_client.table("projects").select("*").eq("user_id", user_id).eq("path", path).execute()

        if not projects.data or len(projects.data) == 0:
            log_step(logger, "Project not found at path", {"path": path})
            raise HTTPException(status_code=404, detail="Project not found at this path")

        proj = projects.data[0]
        log_step(logger, "Project found", {"project_id": proj.get("id"), "name": proj.get("name")})
        
        logger.info(f"STEP: Get project by path complete")
        return ProjectResponse(
            id=str(proj.get("id", "")),
            name=proj.get("name", "Unnamed Project"),
            description=proj.get("description"),
            status=proj.get("status", "new"),
            path=proj.get("path"),
            created_at=str(proj.get("created_at", ""))
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/projects/by-path",
            "path": path,
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=f"Failed to check project: {str(e)}")

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Register a new project"""
    log_step(logger, "Create project request started", {"name": project.name, "path": project.path})
    
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
                "endpoint": "/projects",
                "error_type": "AuthenticationError"
            })
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_id = user_response.user.id
        log_step(logger, "Token validated", {"user_id": user_id})

        log_step(logger, "Checking if project already exists", {"path": project.path})
        # Check if project already exists at this path
        existing = admin_client.table("projects").select("*").eq("user_id", user_id).eq("path", project.path).execute()

        if existing.data and len(existing.data) > 0:
            log_error_with_context(logger, Exception("Project already exists"), {
                "endpoint": "/projects",
                "path": project.path,
                "error_type": "DuplicateError"
            })
            raise HTTPException(status_code=400, detail="Project already exists at this path")

        log_step(logger, "Creating new project in database", {"name": project.name, "path": project.path})
        # Create project
        new_project = admin_client.table("projects").insert({
            "user_id": user_id,
            "name": project.name,
            "path": project.path,
            "description": project.description,
            "status": project.status
        }).execute()

        if not new_project.data:
            log_error_with_context(logger, Exception("Failed to create project"), {
                "endpoint": "/projects",
                "error_type": "DatabaseError"
            })
            raise HTTPException(status_code=500, detail="Failed to create project")

        proj = new_project.data[0]
        log_step(logger, "Project created successfully", {"project_id": proj.get("id"), "name": project.name})
        
        logger.info(f"STEP: Create project complete")
        return ProjectResponse(
            id=str(proj.get("id", "")),
            name=proj.get("name"),
            description=proj.get("description"),
            status=proj.get("status", "new"),
            path=proj.get("path"),
            created_at=str(proj.get("created_at", ""))
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/projects",
            "name": project.name,
            "path": project.path,
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@router.patch("/{project_id}/status")
async def update_project_status(
    project_id: str,
    status: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update project status (new -> in_progress)"""
    log_step(logger, "Update project status request started", {"project_id": project_id, "status": status})
    
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
                "endpoint": "/projects/status",
                "project_id": project_id,
                "error_type": "AuthenticationError"
            })
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_id = user_response.user.id
        log_step(logger, "Token validated", {"user_id": user_id})

        log_step(logger, "Updating project status in database", {"project_id": project_id, "new_status": status})
        # Update status
        result = admin_client.table("projects").update({
            "status": status
        }).eq("id", project_id).eq("user_id", user_id).execute()

        if not result.data:
            log_error_with_context(logger, Exception("Project not found"), {
                "endpoint": "/projects/status",
                "project_id": project_id,
                "user_id": user_id,
                "error_type": "NotFoundError"
            })
            raise HTTPException(status_code=404, detail="Project not found")

        log_step(logger, "Project status updated successfully", {"project_id": project_id, "status": status})
        logger.info(f"STEP: Update project status complete")
        return {"message": "Status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/projects/status",
            "project_id": project_id,
            "status": status,
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a single project"""
    log_step(logger, "Delete project request started", {"project_id": project_id})
    
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
                "endpoint": "/projects/delete",
                "project_id": project_id,
                "error_type": "AuthenticationError"
            })
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_id = user_response.user.id
        log_step(logger, "Token validated", {"user_id": user_id})

        # First verify project exists and belongs to user
        log_step(logger, "Verifying project ownership", {"project_id": project_id, "user_id": user_id})
        existing = admin_client.table("projects").select("id").eq("id", project_id).eq("user_id", user_id).execute()
        
        if not existing.data or len(existing.data) == 0:
            log_error_with_context(logger, Exception("Project not found"), {
                "endpoint": "/projects/delete",
                "project_id": project_id,
                "user_id": user_id,
                "error_type": "NotFoundError"
            })
            raise HTTPException(status_code=404, detail="Project not found or you don't have permission to delete it")

        # Delete conversation history for this project first
        log_step(logger, "Deleting conversation history", {"project_id": project_id})
        try:
            admin_client.table("conversation_history").delete().eq("project_id", project_id).execute()
        except Exception:
            # Table might not exist or no history, continue
            pass

        # Delete the project
        log_step(logger, "Deleting project from database", {"project_id": project_id})
        result = admin_client.table("projects").delete().eq("id", project_id).eq("user_id", user_id).execute()

        if not result.data:
            log_error_with_context(logger, Exception("Failed to delete project"), {
                "endpoint": "/projects/delete",
                "project_id": project_id,
                "error_type": "DatabaseError"
            })
            raise HTTPException(status_code=500, detail="Failed to delete project")

        log_step(logger, "Project deleted successfully", {"project_id": project_id})
        logger.info(f"STEP: Delete project complete")
        return {"message": "Project deleted successfully", "project_id": project_id}
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/projects/delete",
            "project_id": project_id,
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")
