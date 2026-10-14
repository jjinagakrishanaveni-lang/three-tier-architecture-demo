from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of user")
    email: str = Field(..., min_length=5, max_length=255, pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", description="Valid email address")
    password: str = Field(..., min_length=6, max_length=100, description="Password (at least 6 characters)")

class UserVerifyRequest(BaseModel):
    token: str = Field(..., min_length=10, description="Verification token sent via email link")

class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, description="Email address")
    password: str = Field(..., min_length=1, description="Password")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_verified: bool
    created_at: datetime
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RegistrationSuccessResponse(BaseModel):
    message: str
    email: str
    verification_token: str
    verification_url: str
    expires_in_seconds: int

class VerificationSuccessResponse(BaseModel):
    message: str
    user: UserResponse

class SystemStatusResponse(BaseModel):
    status: str
    database: str
    redis: str
    users_count: int
    pending_registrations_count: int
