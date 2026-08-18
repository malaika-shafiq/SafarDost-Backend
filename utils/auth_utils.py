import os
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, JWTError
from pydantic import EmailStr
from sqlalchemy.orm import Session
from models.user import Users
from dotenv import load_dotenv

# 1. Load the hidden .env file variables into memory
load_dotenv()

# 2. Pull the variables securely using os.environ
SECRET_KEY = os.environ.get("SAFARDOST_SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")

# This looks for the "Authorization: Bearer <token>" header automatically
#oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login/swagger")

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    """Transforms plain text into a secure hash using colons only."""
    return bcrypt_context.hash(password)


def authenticate_traveler(email: str, password: str, db: Session):
    """Checks credentials against user database table fields."""
    user = db.query(Users).filter(Users.email == email).first()

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
        "role": role,       # Baked straight into claims data
        "type": "access",   # Helps distinguish token usage
        "exp": token_expiry
    }
    return jwt.encode(token_claims, SECRET_KEY, algorithm=ALGORITHM)


def generate_refresh_token(email: EmailStr, user_id: int, expires_delta: timedelta):
    """Signs a long-lived refresh token (typically 7 days)."""
    token_expiry = datetime.now(timezone.utc) + expires_delta
    token_claims = {
        "sub": email,
        "id": user_id,
        "type": "refresh",  # Prevents users from using this as an access token
        "exp": token_expiry
    }
    return jwt.encode(token_claims, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    """
    Decodes the incoming mobile JWT token synchronously.
    Returns user dictionary context details if valid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials."
    )
    try:
        # Decode the token using secret application key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: EmailStr = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")

        # Guard clause: ensure vital information exists inside the token
        if email is None or user_id is None or role is None:
            raise credentials_exception

        # Return a dictionary containing the authenticated user's identification details
        return {"email": email, "id": user_id, "role": role}

    except JWTError:
        raise credentials_exception


def get_current_admin(current_user: Annotated[dict, Depends(get_current_user)]):
    """
    Dependency gate blocking non-admin user tokens from restricted mutations.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to perform this action."
        )
    return current_user
