from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from database import get_supabase_client, get_supabase_admin_client
from models import (
    UserRegister, UserLogin, ForgotPassword,
    ResetPassword, UserResponse, TokenResponse, RegisterResponse,
    UserProfileUpdate
)
from typing import Union, Dict, Optional
from pydantic import BaseModel
import time
from utils.logger import get_logger, log_step, log_error_with_context

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

# In-memory storage for CLI sessions (session_id -> {token, timestamp})
cli_sessions: Dict[str, Dict[str, any]] = {}

# Clean up old sessions (older than 5 minutes)
def cleanup_old_sessions():
    current_time = time.time()
    expired_sessions = [
        session_id for session_id, data in cli_sessions.items()
        if current_time - data.get("timestamp", 0) > 300  # 5 minutes
    ]
    for session_id in expired_sessions:
        del cli_sessions[session_id]

class CLISessionData(BaseModel):
    session_id: str
    token: str

@router.post("/register", response_model=Union[TokenResponse, RegisterResponse])
async def register(user_data: UserRegister):
    """Register a new user"""
    log_step(logger, "User registration started", {"email": user_data.email})
    
    try:
        log_step(logger, "Getting Supabase client")
        supabase = get_supabase_client()
        
        log_step(logger, "Creating user in Supabase Auth", {"email": user_data.email})
        # Create user in Supabase Auth
        response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "name": user_data.name or ""
                }
            }
        })
        
        log_step(logger, "Sign up response received", {"has_user": bool(response.user), "has_session": bool(response.session)})
        
        # Check for errors in response
        if hasattr(response, 'error') and response.error:
            error_msg = getattr(response.error, 'message', str(response.error))
            log_error_with_context(logger, Exception(error_msg), {
                "endpoint": "/register",
                "email": user_data.email,
                "error_type": "SupabaseError"
            })
            raise HTTPException(status_code=400, detail=error_msg)
        
        if not response.user:
            log_error_with_context(logger, Exception("No user in response"), {
                "endpoint": "/register",
                "email": user_data.email
            })
            raise HTTPException(status_code=400, detail="Registration failed - no user created")
        
        log_step(logger, "User created successfully", {"user_id": response.user.id})
        
        # Get access token - session might be None if email confirmation is required
        session = response.session
        
        user_response = UserResponse(
            id=response.user.id,
            email=response.user.email or "",
            name=user_data.name,
            email_verified=response.user.email_confirmed_at is not None
        )
        
        if not session:
            # Email confirmation required - return success with message
            log_step(logger, "Email confirmation required", {"user_id": response.user.id})
            response_data = RegisterResponse(
                message="Registration successful! Please check your email to confirm your account.",
                user=user_response,
                requires_email_confirmation=True
            )
            logger.info(f"STEP: Registration complete - email confirmation required")
            return response_data

        # Session exists - return token response
        log_step(logger, "Session exists - returning token", {"user_id": response.user.id})
        response_data = TokenResponse(
            access_token=session.access_token,
            user=user_response
        )
        logger.info(f"STEP: Registration complete - user authenticated")
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/register",
            "email": user_data.email,
            "error_type": type(e).__name__
        })
        error_detail = str(e)
        raise HTTPException(status_code=400, detail=error_detail)

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login user"""
    log_step(logger, "User login started", {"email": credentials.email})
    
    try:
        log_step(logger, "Getting Supabase client")
        supabase = get_supabase_client()
        
        log_step(logger, "Attempting password authentication")
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if not response.user or not response.session:
            log_error_with_context(logger, Exception("Invalid credentials"), {
                "endpoint": "/login",
                "email": credentials.email,
                "error_type": "AuthenticationError"
            })
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        log_step(logger, "Authentication successful", {"user_id": response.user.id})
        
        # Get user profile from database
        log_step(logger, "Fetching user profile from database")
        admin_client = get_supabase_admin_client()
        user_profile = admin_client.table("users").select("*").eq("id", response.user.id).execute()
        
        user_name = None
        if user_profile.data:
            user_name = user_profile.data[0].get("name")
            log_step(logger, "User profile retrieved", {"name": user_name})
        
        logger.info(f"STEP: Login complete - user authenticated")
        return TokenResponse(
            access_token=response.session.access_token,
            user=UserResponse(
                id=response.user.id,
                email=response.user.email or "",
                name=user_name,
                email_verified=response.user.email_confirmed_at is not None
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/login",
            "email": credentials.email,
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword):
    """Send password reset email"""
    log_step(logger, "Forgot password request started", {"email": data.email})
    
    try:
        log_step(logger, "Getting Supabase client")
        supabase = get_supabase_client()
        
        log_step(logger, "Sending password reset email")
        response = supabase.auth.reset_password_for_email(
            data.email,
            {
                "redirect_to": "http://localhost:3000/reset-password"
            }
        )
        
        log_step(logger, "Password reset email sent successfully", {"email": data.email})
        logger.info(f"STEP: Forgot password complete")
        return {"message": "Password reset email sent"}
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/forgot-password",
            "email": data.email,
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset-password")
async def reset_password(data: ResetPassword):
    """Reset password with token"""
    log_step(logger, "Reset password request started")
    
    try:
        log_step(logger, "Getting Supabase client")
        supabase = get_supabase_client()
        
        log_step(logger, "Validating reset token")
        # Exchange the token for a session, then update password
        response = supabase.auth.set_session(access_token=data.token, refresh_token="")
        if response.user:
            log_step(logger, "Token validated, updating password", {"user_id": response.user.id})
            supabase.auth.update_user({
                "password": data.password
            })
            log_step(logger, "Password updated successfully")
            logger.info(f"STEP: Reset password complete")
            return {"message": "Password reset successful"}
        else:
            log_error_with_context(logger, Exception("Invalid or expired token"), {
                "endpoint": "/reset-password",
                "error_type": "TokenError"
            })
            raise HTTPException(status_code=400, detail="Invalid or expired token")
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/reset-password",
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=400, detail="Invalid or expired token")

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user"""
    log_step(logger, "Logout request started")
    
    try:
        log_step(logger, "Getting Supabase client")
        supabase = get_supabase_client()
        
        log_step(logger, "Signing out user")
        supabase.auth.set_session(access_token=credentials.credentials, refresh_token="")
        supabase.auth.sign_out()
        
        log_step(logger, "User logged out successfully")
        logger.info(f"STEP: Logout complete")
        return {"message": "Logged out successfully"}
    except Exception as e:
        # Even if there's an error, consider it logged out
        log_step(logger, "Logout completed (with error)", {"error": str(e)})
        logger.info(f"STEP: Logout complete (error handled)")
        return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    log_step(logger, "Get current user request started")
    
    try:
        log_step(logger, "Getting Supabase client")
        supabase = get_supabase_client()
        
        log_step(logger, "Validating user token")
        user_response = supabase.auth.get_user(credentials.credentials)

        if not user_response.user:
            log_error_with_context(logger, Exception("Not authenticated"), {
                "endpoint": "/me",
                "error_type": "AuthenticationError"
            })
            raise HTTPException(status_code=401, detail="Not authenticated")

        log_step(logger, "Token validated", {"user_id": user_response.user.id})

        # Get user profile from database
        log_step(logger, "Fetching user profile from database")
        admin_client = get_supabase_admin_client()
        user_profile = admin_client.table("users").select("*").eq("id", user_response.user.id).execute()

        user_data = {}
        if user_profile.data and len(user_profile.data) > 0:
            user_data = user_profile.data[0]
            log_step(logger, "User profile retrieved", {"has_profile": True})
        else:
            log_step(logger, "No profile data found", {"user_id": user_response.user.id})

        logger.info(f"STEP: Get current user complete")
        return UserResponse(
            id=user_response.user.id,
            email=user_response.user.email or "",
            name=user_data.get("name"),
            email_verified=user_response.user.email_confirmed_at is not None,
            experience_level=user_data.get("experience_level"),
            tech_knowledge=user_data.get("tech_knowledge") or [],
            coding_ability=user_data.get("coding_ability"),
            tool_preference=user_data.get("tool_preference"),
            help_level=user_data.get("help_level"),
            ai_tools=user_data.get("ai_tools") or [],
            primary_goal=user_data.get("primary_goal"),
            time_commitment=user_data.get("time_commitment"),
            team_or_solo=user_data.get("team_or_solo"),
            previous_projects=user_data.get("previous_projects"),
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/me",
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=401, detail="Not authenticated")

@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update user profile"""
    log_step(logger, "Profile update request started")
    
    try:
        log_step(logger, "Getting Supabase client")
        supabase = get_supabase_client()
        
        log_step(logger, "Validating user token")
        user_response = supabase.auth.get_user(credentials.credentials)

        if not user_response.user:
            log_error_with_context(logger, Exception("Not authenticated"), {
                "endpoint": "/profile",
                "error_type": "AuthenticationError"
            })
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_id = user_response.user.id
        log_step(logger, "Token validated", {"user_id": user_id})
        
        admin_client = get_supabase_admin_client()

        # Prepare update data (only include fields that were set)
        # Support both Pydantic v1 and v2
        if hasattr(profile_data, 'model_dump'):
            update_data = profile_data.model_dump(exclude_unset=True)
        else:
            update_data = profile_data.dict(exclude_unset=True)

        log_step(logger, "Preparing update data", {"fields": list(update_data.keys())})

        # Update user profile
        log_step(logger, "Updating user profile in database")
        result = admin_client.table("users").update(update_data).eq("id", user_id).execute()

        if not result.data:
            log_error_with_context(logger, Exception("User not found"), {
                "endpoint": "/profile",
                "user_id": user_id,
                "error_type": "NotFoundError"
            })
            raise HTTPException(status_code=404, detail="User not found")

        updated_profile = result.data[0]
        log_step(logger, "Profile updated successfully", {"user_id": user_id})

        logger.info(f"STEP: Profile update complete")
        # Return updated user response
        return UserResponse(
            id=user_response.user.id,
            email=user_response.user.email or "",
            name=updated_profile.get("name"),
            email_verified=user_response.user.email_confirmed_at is not None,
            experience_level=updated_profile.get("experience_level"),
            tech_knowledge=updated_profile.get("tech_knowledge") or [],
            coding_ability=updated_profile.get("coding_ability"),
            tool_preference=updated_profile.get("tool_preference"),
            help_level=updated_profile.get("help_level"),
            ai_tools=updated_profile.get("ai_tools") or [],
            primary_goal=updated_profile.get("primary_goal"),
            time_commitment=updated_profile.get("time_commitment"),
            team_or_solo=updated_profile.get("team_or_solo"),
            previous_projects=updated_profile.get("previous_projects"),
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/profile",
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@router.post("/cli-session")
async def store_cli_session(data: CLISessionData):
    """Store token for CLI session (called by web frontend after login)"""
    log_step(logger, "Store CLI session request started", {"session_id": data.session_id})
    
    try:
        log_step(logger, "Cleaning up old sessions")
        cleanup_old_sessions()
        
        log_step(logger, "Storing CLI session")
        cli_sessions[data.session_id] = {
            "token": data.token,
            "timestamp": time.time()
        }
        log_step(logger, "CLI session stored successfully", {"session_id": data.session_id})
        logger.info(f"STEP: Store CLI session complete")
        return {"message": "Session stored successfully"}
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/cli-session",
            "session_id": data.session_id,
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail="Failed to store session")

@router.get("/cli-session/{session_id}")
async def get_cli_session(session_id: str):
    """Get token for CLI session (polled by CLI)"""
    log_step(logger, "Get CLI session request started", {"session_id": session_id})
    
    try:
        log_step(logger, "Cleaning up old sessions")
        cleanup_old_sessions()

        if session_id not in cli_sessions:
            log_error_with_context(logger, Exception("Session not found"), {
                "endpoint": "/cli-session",
                "session_id": session_id,
                "error_type": "NotFoundError"
            })
            raise HTTPException(status_code=404, detail="Session not found or expired")

        log_step(logger, "Session found, retrieving token")
        session_data = cli_sessions[session_id]
        token = session_data.get("token")

        log_step(logger, "Validating token")
        # Verify the token is valid
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(token)

        if not user_response.user:
            # Invalid token, remove it
            log_error_with_context(logger, Exception("Invalid token"), {
                "endpoint": "/cli-session",
                "session_id": session_id,
                "error_type": "TokenError"
            })
            del cli_sessions[session_id]
            raise HTTPException(status_code=401, detail="Invalid token")

        log_step(logger, "Token validated, fetching user profile", {"user_id": user_response.user.id})
        # Get user profile
        admin_client = get_supabase_admin_client()
        user_profile = admin_client.table("users").select("*").eq("id", user_response.user.id).execute()

        user_name = None
        if user_profile.data and len(user_profile.data) > 0:
            user_name = user_profile.data[0].get("name")

        log_step(logger, "Removing session (one-time use)", {"session_id": session_id})
        # Remove session after successful retrieval (one-time use)
        del cli_sessions[session_id]

        log_step(logger, "CLI session retrieved successfully")
        logger.info(f"STEP: Get CLI session complete")
        return {
            "token": token,
            "user": {
                "id": user_response.user.id,
                "email": user_response.user.email or "",
                "name": user_name,
                "email_verified": user_response.user.email_confirmed_at is not None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error_with_context(logger, e, {
            "endpoint": "/cli-session",
            "session_id": session_id,
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail="Failed to retrieve session")

