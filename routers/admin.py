from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import Users
from schemas.auth_schemas import UserResponse  # Reuse your user schema
from utils.auth_utils import get_current_admin  # Secure Dependency

# 🔒 Any endpoint inside this router automatically requires Admin role checking!
router = APIRouter(
    prefix="/admin",
    tags=["Admin Management"],
    dependencies=[Depends(get_current_admin)]
)

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/users", response_model=list[UserResponse])
def get_all_users(db: db_dependency):
    """
    ADMIN ONLY: View all accounts across Pakistan (both active and soft-deleted).
    """
    return db.query(Users).all()


@router.put("/users/{user_id}/restore", status_code=status.HTTP_200_OK)
def restore_soft_deleted_user(user_id: int, db: db_dependency):
    """
    ADMIN ONLY: Reverse a soft delete by turning an inactive traveler account back on.
    """
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.status = "y"  # Reactivate account
    db.commit()
    return {"message": f"User account {user.email} successfully restored."}


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
