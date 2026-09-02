import os
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, JWTError
from pydantic import EmailStr
from sqlalchemy.orm import Session
from models.user import Users, UserStatusEnum  # 👈 Imported your Enum here
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SECRET_KEY = os.environ.get("SAFARDOST_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("CRITICAL ERROR: SAFARDOST_SECRET_KEY environment variable is not set!")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")

# OAuth2 setup for Swagger docs
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login/swagger")

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    """Transforms plain text into a secure hash."""
    return bcrypt_context.hash(password)


def authenticate_traveler(email: str, password: str, db: Session):
    """
    Looks up a user record and matches hashes.
    Filters exclusively for active enum values instead of old strings.
    """
    # 👈 FIX: Filter updated from status == "y" to status == UserStatusEnum.active
    user = db.query(Users).filter(
        Users.email == email,
        Users.status == UserStatusEnum.active
    ).first()

    if not user:
        return None

    if not bcrypt_context.verify(password, user.hashed_password):
        return None

    return user


def generate_access_token(email: str, user_id: int, role: str, expires_delta: timedelta):
    """Signs a short-lived access token containing role scopes."""
    token_expiry = datetime.now(timezone.utc) + expires_delta
    token_claims = {
        "sub": email,
        "id": user_id,
        "role": role,
        "type": "access",
        "exp": token_expiry
    }
    return jwt.encode(token_claims, SECRET_KEY, algorithm=ALGORITHM)


def generate_refresh_token(email: EmailStr, user_id: int, expires_delta: timedelta):
    """Signs a long-lived refresh token."""
    token_expiry = datetime.now(timezone.utc) + expires_delta
    token_claims = {
        "sub": email,
        "id": user_id,
        "type": "refresh",
        "exp": token_expiry
    }
    return jwt.encode(token_claims, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    """Decodes the incoming mobile JWT token synchronously."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials."
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: EmailStr = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")

        if email is None or user_id is None or role is None:
            raise credentials_exception

        return {"email": email, "id": user_id, "role": role}

    except JWTError:
        raise credentials_exception


def get_current_admin(current_user: Annotated[dict, Depends(get_current_user)]):
    """Dependency gate blocking non-admin user tokens."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to perform this action."
        )
    return current_user
