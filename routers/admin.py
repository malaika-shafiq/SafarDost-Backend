from typing import Annotated, Optional
import math
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session
from database import get_db
from models.user import Users, UserStatusEnum
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
# Reusing individual user schema and the new paginated structure from your auth_schemas
from schemas.auth_schemas import UserResponse, PaginatedUserResponse, AdminUserStatsResponse
# Ensure you import AdminUserUpdate and AdminRoleUpdate at the top of your routers/admin.py file
from schemas.auth_schemas import AdminUserUpdate, AdminRoleUpdate
from utils.auth_utils import get_current_admin

# 🔒 Any endpoint inside this router automatically requires Admin role checking!
router = APIRouter(
    prefix="/admin",
    tags=["Admin Management"],
    dependencies=[Depends(get_current_admin)]
)

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/users", response_model=PaginatedUserResponse)
def get_all_users(
        db: db_dependency,
        page: int = Query(1, ge=1, description="Page number starting from 1"),
        limit: int = Query(25, ge=1, le=100, description="Number of items per page"),
        search: Optional[str] = Query(None, description="Search across traveler name or email"),
        role: Optional[str] = Query(None, description="Filter by role (e.g., traveler, admin)"),
        status_filter: Optional[UserStatusEnum] = Query(None, alias="status",
                                                        description="Filter by account status enum"),
        sort_by: str = Query("id", description="Field to sort database records by"),
        order: str = Query("desc", description="Sort execution order (asc or desc)")
):
    """
    ADMIN ONLY: View accounts with server-side pagination, query filtering, and dynamic sorting.
    """
    # 1. Initialize Base Query
    query = db.query(Users)

    # 2. Server-Side Filtering Implementation
    if search:
        query = query.filter(
            or_(
                Users.email.ilike(f"%{search}%"),
                Users.name.ilike(f"%{search}%")
            )
        )

    if role:
        query = query.filter(Users.role == role)

    if status_filter:
        query = query.filter(Users.status == status_filter)

    # 3. Dynamic Sorting Process
    sort_column = getattr(Users, sort_by, Users.id)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # 4. Extract Overall Record Counts
    total_items = query.count()

    # 5. Offset Calculations & DB Limit Isolation
    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()

    # 6. Pagination Metadata Logic
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0

    # 7. Deliver Synchronized Payload Wrapped Structure
    return {
        "items": items,
        "total": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


@router.get("/users/stats", response_model=AdminUserStatsResponse)
def get_user_management_stats(db: db_dependency):
    """
    ADMIN ONLY: Fetch a lightweight overview of system metrics and dashboard KPIs.
    Avoids loading full user records into memory by processing counts at the database level.
    """
    # 1. Calculate the timestamp boundary for 7 days ago
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # 2. Perform lightning-fast counts at the database layer
    total_users = db.query(func.count(Users.id)).scalar()

    active_users = db.query(func.count(Users.id)) \
        .filter(Users.status == UserStatusEnum.active).scalar()

    travelers_count = db.query(func.count(Users.id)) \
        .filter(Users.role == "traveler").scalar()

    admins_count = db.query(func.count(Users.id)) \
        .filter(Users.role == "admin").scalar()

    guides_count = db.query(func.count(Users.id)) \
        .filter(Users.role == "guide").scalar()

    new_this_week = db.query(func.count(Users.id)) \
        .filter(Users.created_at >= one_week_ago).scalar()

    # 3. Deliver exactly the key structure requested by your supervisor
    return {
        "total_users": total_users or 0,
        "active_users": active_users or 0,
        "travelers": travelers_count or 0,
        "admins": admins_count or 0,
        "guides": guides_count or 0,
        "new_this_week": new_this_week or 0
    }


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user_details(user_id: int, payload: AdminUserUpdate, db: db_dependency):
    """
    ADMIN ONLY: Update any traveler profile information (Name, Email, Phone, CNIC).
    """
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Convert incoming data to a dictionary, ignoring any field left blank
    update_data = payload.model_dump(exclude_unset=True)

    # Check email unique constraint if email is being updated
    if "email" in update_data and update_data["email"] != user.email:
        email_exists = db.query(Users).filter(Users.email == update_data["email"]).first()
        if email_exists:
            raise HTTPException(status_code=400, detail="Email is already registered.")

    # Dynamically update only the fields sent in the request
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(user_id: int, payload: AdminRoleUpdate, db: db_dependency):
    """
    ADMIN ONLY: Partially update user security clearance (traveler ➔ guide / admin).
    """
    # Whitelist including the guide role exactly as your supervisor requested
    allowed_roles = ["admin", "traveler", "guide"]
    if payload.role.lower() not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Allowed roles are: {', '.join(allowed_roles)}"
        )

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.role = payload.role.lower()
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/suspend", status_code=status.HTTP_200_OK)
def suspend_soft_delete_user(user_id: int, db: db_dependency):
    """
    ADMIN ONLY: Suspend an account safely using descriptive enums.
    """
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.status == UserStatusEnum.suspended:
        raise HTTPException(status_code=400, detail="Account is already suspended.")

    user.status = UserStatusEnum.suspended  # Apply Enum
    db.commit()
    return {"message": f"User account {user.email} successfully suspended."}


@router.put("/users/{user_id}/restore", status_code=status.HTTP_200_OK)
def restore_soft_deleted_user(user_id: int, db: db_dependency):
    """
    ADMIN ONLY: Reactivate a traveler account by flipping status to active.
    """
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.status = UserStatusEnum.active  # Apply Enum
    db.commit()
    return {"message": f"User account {user.email} successfully restored to active state."}


@router.delete("/users/{user_id}/purge", status_code=status.HTTP_200_OK)
def permanently_purge_user(user_id: int, db: db_dependency):
    """
    ADMIN ONLY: Hard delete a malicious user permanently from the database table.
    """
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    db.delete(user)
    db.commit()
    return {"message": "Account permanently purged from database disk storage."}
