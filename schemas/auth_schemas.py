from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    name: str
    email: EmailStr  # Automatically validates proper formats (e.g; user@email.com)
    password: str    # Plain text password from frontend
    role: Optional[str] = "traveler"  # Options: "admin", "traveler"


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True  # Allows Pydantic to read classic SQLAlchemy columns easily


class UserLogin(BaseModel):
    email: EmailStr  # Ensures the mobile app passes a valid email structure
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str  # Add this to pass the long-lived key to the mobile app
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)
