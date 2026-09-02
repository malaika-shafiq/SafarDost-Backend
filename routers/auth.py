from datetime import timedelta
from typing import Annotated
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import Session
from database import get_db
from models.user import Users, UserStatusEnum  # 👈 Imported your Enum here
from schemas import auth_schemas
from schemas.auth_schemas import PasswordUpdate, TokenRefreshRequest
from utils.auth_utils import (
    get_current_user, hash_password, authenticate_traveler, bcrypt_context,
    generate_access_token, generate_refresh_token, SECRET_KEY, ALGORITHM
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post("/register", response_model=auth_schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_request: auth_schemas.UserCreate, db: db_dependency):
    """Registers a new traveler account or admin profile for Safar Dost Pakistan."""
    existing_user = db.query(Users).filter(Users.email == user_request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    input_role = user_request.role.strip().lower() if user_request.role else "traveler"

    if input_role == "admin" and True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public creation of administrator accounts is prohibited."
        )

    user_payload = user_request.model_dump()
    plain_password = user_payload.pop("password")
    user_payload.pop("role", None)

    db_user = Users(
        **user_payload,
        hashed_password=hash_password(plain_password),
        role=input_role,
        status=UserStatusEnum.active  # 👈 FIX: Set default registration state to Enum
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=auth_schemas.TokenResponse, status_code=status.HTTP_200_OK)
def login_user(login_request: auth_schemas.UserLogin, db: db_dependency):
    """Authenticates a user and returns tokens along with their profile data."""
    user = authenticate_traveler(login_request.email, login_request.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = generate_access_token(
        email=user.email,
        user_id=user.id,
        role=getattr(user, "role", "traveler"),
        expires_delta=timedelta(minutes=15)
    )

    refresh_token = generate_refresh_token(
        email=user.email,
        user_id=user.id,
        expires_delta=timedelta(days=30)
    )

    user.current_refresh_token = refresh_token
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login/swagger", include_in_schema=True)
def login_user_for_swagger(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Dedicated authentication route specifically for Swagger UI forms."""
    input_email = str(form_data.username).strip()
    input_password = str(form_data.password)

    user = authenticate_traveler(input_email, input_password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = generate_access_token(
        email=str(user.email),
        user_id=int(user.id),
        role=str(getattr(user, "role", "traveler")),
        expires_delta=timedelta(minutes=15)
    )

    refresh_token = generate_refresh_token(
        email=str(user.email),
        user_id=int(user.id),
        expires_delta=timedelta(days=30)
    )

    user.current_refresh_token = refresh_token
    db.add(user)
    db.commit()

    return {
        "access_token": str(access_token),
        "refresh_token": str(refresh_token),
        "token_type": "bearer"
    }


@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh_access_token(refresh_request: TokenRefreshRequest, db: db_dependency):
    """Validates a refresh token against the database to protect against reuse attacks."""
    try:
        payload = jwt.decode(refresh_request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: EmailStr = payload.get("sub")
        user_id: int = payload.get("id")
        token_type: str = payload.get("type")

        if email is None or user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload parameters."
            )

        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User does not exist.")

        if user.current_refresh_token != refresh_request.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is revoked or no longer active. Please log in again."
            )

        new_access_token = generate_access_token(
            email=user.email,
            user_id=user.id,
            role=getattr(user, "role", "traveler"),
            expires_delta=timedelta(minutes=15)
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired or is invalid. Please log in again."
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout_user(current_user: user_dependency, db: db_dependency):
    """Logs out the user by revoking their current refresh token."""
    user = db.query(Users).filter(Users.id == current_user.get("id")).first()
    if user:
        user.current_refresh_token = None
        db.add(user)
        db.commit()
    return {"message": "Successfully logged out."}


@router.put("/change-password", status_code=status.HTTP_200_OK)
def change_user_password(password_request: PasswordUpdate, current_user: user_dependency, db: db_dependency):
    """Allows an authenticated user to securely change their login password."""
    user = db.query(Users).filter(Users.id == current_user.get("id")).first()

    if not user or not bcrypt_context.verify(password_request.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed. Please try again."
        )

    user.hashed_password = hash_password(password_request.new_password)
    db.add(user)
    db.commit()
    return {"message": "Password updated successfully!"}


@router.get("/me", response_model=auth_schemas.UserResponse, status_code=status.HTTP_200_OK)
def get_current_user_profile(current_user: user_dependency, db: db_dependency):
    """Fetches the logged-in user's profile details."""
    user = db.query(Users).filter(Users.id == current_user.get("id")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found."
        )
    return user


@router.delete("/account", status_code=status.HTTP_200_OK)
def delete_user_account(current_user: user_dependency, db: db_dependency):
    """Soft deletes/deactivates a user's account by switching status to 'inactive'."""
    user = db.query(Users).filter(Users.id == current_user.get("id")).first()

    if user and user.role.lower() == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System administration accounts cannot be deactivated via public channels."
        )

    # 👈 FIX: Filter condition updated from user.status == "n" to UserStatusEnum.inactive
    if not user or user.status == UserStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or already deactivated."
        )

    # 👈 FIX: Value assignment updated from "n" to UserStatusEnum.inactive
    user.status = UserStatusEnum.inactive
    user.current_refresh_token = None

    db.add(user)
    db.commit()
    return {"message": "Your account has been deactivated successfully."}
