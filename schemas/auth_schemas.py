from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "traveler"
    phone_number: Optional[str] = None  # Optional field
    cnic_number: Optional[str] = None   # Optional field

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    phone_number: Optional[str]
    cnic_number: Optional[str]
    status: str

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr  # Ensures the mobile app passes a valid email structure
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse  # This will now return the full logged-in user profile


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)
