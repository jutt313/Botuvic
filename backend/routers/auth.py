from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from database import get_supabase_client, get_supabase_admin_client
from models import (
    UserRegister, UserLogin, ForgotPassword,
    ResetPassword, UserResponse, TokenResponse, RegisterResponse
)
from typing import Union
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

@router.post("/register", response_model=Union[TokenResponse, RegisterResponse])
async def register(user_data: UserRegister):
    """Register a new user"""
    try:
        supabase = get_supabase_client()
        
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
        
        logger.info(f"Sign up response: {response}")
        
        # Check for errors in response
        if hasattr(response, 'error') and response.error:
            error_msg = getattr(response.error, 'message', str(response.error))
            logger.error(f"Supabase error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        if not response.user:
            logger.error("No user in response")
            raise HTTPException(status_code=400, detail="Registration failed - no user created")
        
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
            logger.info("Email confirmation required")
            response_data = RegisterResponse(
                message="Registration successful! Please check your email to confirm your account.",
                user=user_response,
                requires_email_confirmation=True
            )
            logger.info(f"Returning RegisterResponse: {response_data}")
            return response_data

        # Session exists - return token response
        response_data = TokenResponse(
            access_token=session.access_token,
            user=user_response
        )
        logger.info(f"Returning TokenResponse")
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        error_detail = str(e)
        raise HTTPException(status_code=400, detail=error_detail)

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login user"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if not response.user or not response.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Get user profile from database
        admin_client = get_supabase_admin_client()
        user_profile = admin_client.table("users").select("*").eq("id", response.user.id).execute()
        
        user_name = None
        if user_profile.data:
            user_name = user_profile.data[0].get("name")
        
        return TokenResponse(
            access_token=response.session.access_token,
            user=UserResponse(
                id=response.user.id,
                email=response.user.email or "",
                name=user_name,
                email_verified=response.user.email_confirmed_at is not None
            )
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword):
    """Send password reset email"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.auth.reset_password_for_email(
            data.email,
            {
                "redirect_to": "http://localhost:3000/reset-password"
            }
        )
        
        return {"message": "Password reset email sent"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset-password")
async def reset_password(data: ResetPassword):
    """Reset password with token"""
    try:
        supabase = get_supabase_client()
        
        # Exchange the token for a session, then update password
        response = supabase.auth.set_session(access_token=data.token, refresh_token="")
        if response.user:
            supabase.auth.update_user({
                "password": data.password
            })
            return {"message": "Password reset successful"}
        else:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user"""
    try:
        supabase = get_supabase_client()
        supabase.auth.set_session(access_token=credentials.credentials, refresh_token="")
        supabase.auth.sign_out()
        
        return {"message": "Logged out successfully"}
    except Exception as e:
        # Even if there's an error, consider it logged out
        return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(credentials.credentials)
        
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get user profile from database
        admin_client = get_supabase_admin_client()
        user_profile = admin_client.table("users").select("*").eq("id", user_response.user.id).execute()
        
        user_name = None
        if user_profile.data and len(user_profile.data) > 0:
            user_name = user_profile.data[0].get("name")
        
        return UserResponse(
            id=user_response.user.id,
            email=user_response.user.email or "",
            name=user_name,
            email_verified=user_response.user.email_confirmed_at is not None
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Not authenticated")

