from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    password: str

class UserProfileUpdate(BaseModel):
    experience_level: Optional[str] = None
    tech_knowledge: Optional[List[str]] = None
    coding_ability: Optional[str] = None
    tool_preference: Optional[str] = None
    help_level: Optional[str] = None
    ai_tools: Optional[List[str]] = None
    primary_goal: Optional[str] = None
    time_commitment: Optional[str] = None
    team_or_solo: Optional[str] = None
    previous_projects: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    email_verified: bool = False
    experience_level: Optional[str] = None
    tech_knowledge: Optional[List[str]] = None
    coding_ability: Optional[str] = None
    tool_preference: Optional[str] = None
    help_level: Optional[str] = None
    ai_tools: Optional[List[str]] = None
    primary_goal: Optional[str] = None
    time_commitment: Optional[str] = None
    team_or_solo: Optional[str] = None
    previous_projects: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class RegisterResponse(BaseModel):
    message: str
    user: Optional[UserResponse] = None
    requires_email_confirmation: bool = False

