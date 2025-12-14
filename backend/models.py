from pydantic import BaseModel, EmailStr
from typing import Optional

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

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    email_verified: bool = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class RegisterResponse(BaseModel):
    message: str
    user: Optional[UserResponse] = None
    requires_email_confirmation: bool = False

