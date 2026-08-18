from datetime import timedelta
from typing import Annotated
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm  # ADDED THIS IMPORT FOR SWAGGER UI LOGIN
from pydantic import EmailStr
from sqlalchemy.orm import Session
from database import get_db
from models.user import Users
from schemas import auth_schemas
from schemas.auth_schemas import PasswordUpdate, TokenRefreshRequest
from utils.auth_utils import get_current_user, hash_password, authenticate_traveler, bcrypt_context, \
    generate_access_token, generate_refresh_token, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["Authentication"])


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post("/register", response_model=auth_schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_request: auth_schemas.UserCreate, db: db_dependency):
    """
    Registers a new traveler account or admin profile for TravelMate Pakistan.
    """
    # 1. Guard against email reuse
    existing_user = db.query(Users).filter(Users.email == user_request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Clean the input role safely
    input_role = user_request.role.strip().lower() if user_request.role else "traveler"

    # 2. PROD SAFETY GUARD: Prevents malicious users from registering as administrators.
    # Note: When creating very first admin profile, change True to False temporarily,
    # run signup request via Thunder Client, then set it back to True to lock the system down!
    if input_role == "admin" and True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public creation of administrator accounts is prohibited."
        )

    # 3. Extract database creation mapping safely using dictionary management
    user_payload = user_request.model_dump()
    plain_password = user_payload.pop("password")
    user_payload.pop("role", None)  # Safeguards against missing disk column exceptions

    # Explicit mapping architecture matching the column fields precisely
    db_user = Users(
        **user_payload,
        hashed_password=hash_password(plain_password),
        role=input_role  # Injected directly into SQLAlchemy attribute hook safely
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login", response_model=auth_schemas.TokenResponse, status_code=status.HTTP_200_OK)
def login_user(login_request: auth_schemas.UserLogin, db: db_dependency):
    """
    Authenticates a traveler and returns both an access and refresh token.
    """
    user = authenticate_traveler(login_request.email, login_request.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Generate a 15-minute short access token containing the role mapping
    access_token = generate_access_token(
        email=user.email,
        user_id=user.id,
        role=getattr(user, "role", "traveler"),  # Safe dynamic attribute access fallback
        expires_delta=timedelta(minutes=15)
    )

    # Generate a 30-day long refresh token
    refresh_token = generate_refresh_token(
        email=user.email,
        user_id=user.id,
        expires_delta=timedelta(days=30)
    )

    user.current_refresh_token = refresh_token
    db.add(user)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/login/swagger", include_in_schema=True)
def login_user_for_swagger(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Dedicated authentication route specifically for Swagger UI's Authorize dialog form box.
    """
    input_email = str(form_data.username).strip()
    input_password = str(form_data.password)

    user = authenticate_traveler(input_email, input_password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # 1. Generate a standard short access token containing role mappings
    access_token = generate_access_token(
        email=str(user.email),
        user_id=int(user.id),
        role=str(getattr(user, "role", "traveler")),
        expires_delta=timedelta(minutes=15)
    )

    # 2. Generate the 30-day long refresh token to keep your DB state perfect
    refresh_token = generate_refresh_token(
        email=str(user.email),
        user_id=int(user.id),
        expires_delta=timedelta(days=30)
    )

    # 3. Save the token state down to your users table in SQLite
    user.current_refresh_token = refresh_token
    db.add(user)
    db.commit()

    # 4. FIX APPLIED: Return ALL matching data keys to satisfy Pydantic's TokenResponse model fields
    return {
        "access_token": str(access_token),
        "refresh_token": str(refresh_token),  # Added key to prevent schema validation failures!
        "token_type": "bearer"
    }



@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh_access_token(refresh_request: TokenRefreshRequest, db: db_dependency):
    """
    Validates a refresh token against the database to protect against reuse attacks.
    """
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

        # Fetch the user from the database
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User does not exist.")

        # ---- HARDENING VERIFICATION ----
        # If the token passed doesn't match the database or is None (logged out), block them immediately
        if user.current_refresh_token != refresh_request.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is revoked or no longer active. Please log in again."
            )

        # Generate a fresh 15-minute access token, passing the structural role argument cleanly
        new_access_token = generate_access_token(
            email=user.email,
            user_id=user.id,
            role=getattr(user, "role", "traveler"),  # Safe dynamic attribute access fallback
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
    """
    Logs out the traveler by revoking their current refresh token in the database.
    """
    user = db.query(Users).filter(Users.id == current_user.get("id")).first()

    if user:
        # Clear the database column. This instantly kills the active refresh token session!
        user.current_refresh_token = None
        db.add(user)
        db.commit()

    return {"message": "Successfully logged out. Mobile session terminated."}


@router.put("/change-password", status_code=status.HTTP_200_OK)
def change_user_password(password_request: PasswordUpdate, current_user: user_dependency, db: db_dependency):
    """
    Allows an authenticated traveler to securely change their login password.
    """
    # 1. Pull the traveler's record out of the database using the ID from their JWT token
    user = db.query(Users).filter(Users.id == current_user.get("id")).first()

    # 2. Defensive Check: Verify their old password matches the database hash
    if not user or not bcrypt_context.verify(password_request.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed. Please try again."
        )

    # 3. Scramble the new password using clean utility helper
    user.hashed_password = hash_password(password_request.new_password)

    # 4. Save updates into local SQLite file
    db.add(user)
    db.commit()

    return {"message": "Password updated successfully!"}


@router.get("/me", response_model=auth_schemas.UserResponse, status_code=status.HTTP_200_OK)
def get_current_user_profile(current_user: user_dependency, db: db_dependency):
    """
    Fetches the logged-in traveler's account profile details using their active mobile session token.
    """
    # 1. Look up the specific user by the secure ID stored inside their JWT claim payload
    user = db.query(Users).filter(Users.id == current_user.get("id")).first()

    # 2. Defensive Guard Clause: Ensure the account still actively exists in safardost.db
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found."
        )

    # 3. Return the database user row, which automatically mirrors clean UserResponse schema shape
    return user


@router.delete("/account", status_code=status.HTTP_200_OK)
def delete_user_account(current_user: user_dependency, db: db_dependency):
    """
    Permanently deletes a traveler's account and profile data from TravelMate Pakistan.
    """
    # 1. Fetch the user profile by tracking the secure ID in the JWT session token
    user = db.query(Users).filter(Users.id == current_user.get("id")).first()

    # 2. Defensive Guard Clause: Verify the account exists before executing deletion
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or already deleted."
        )

    # 3. Remove the target record row from the SQLite engine cache
    db.delete(user)
    db.commit()

    # 4. Return a clean confirmation dictionary to alert the mobile app to purge local device data
    return {"message": "Your traveler account has been permanently deleted successfully."}
