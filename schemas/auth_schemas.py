from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from models.user import UserStatusEnum

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
    status: UserStatusEnum
    # 🕒 INCLUDE TIMESTAMPS IN RESPONSE
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

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


class PaginatedUserResponse(BaseModel):
    items: List[UserResponse]  # Reuses your existing individual user schema
    total: int
    page: int
    limit: int
    total_pages: int


# For general profile updates (PUT)
class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    cnic_number: Optional[str] = None

# For targeted role modification (PATCH)
class AdminRoleUpdate(BaseModel):
    role: str = Field(..., description="Must be 'admin', 'traveler', or 'guide'")


class AdminUserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    travelers: int
    admins: int
    guides: int
    new_this_week: int