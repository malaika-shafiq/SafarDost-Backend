import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile
from typing import Annotated, List, Optional
from sqlalchemy.orm import Session
from database import get_db
from models.review import Reviews
from models.place import Places
from models.hotel import Hotels
from models.restaurant import Restaurants
from schemas.review_schemas import ReviewResponse, ReviewUpdate
from utils.auth_utils import get_current_user

logger = logging.getLogger("safardost.reviews")

router = APIRouter(prefix="/reviews", tags=["Reviews Management"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

# ⚡ OPTIMIZATION: Setup absolute static file directory path parameters on server hard drive
UPLOAD_DIR = os.path.join("static", "uploads", "reviews")
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Auto-creates the folder maps on startup boot if missing


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
        db: db_dependency,
        current_user: user_dependency,
        rating: int = Form(..., ge=1, le=5, description="Star score restricted between 1 and 5"),
        comment: str = Form(..., min_length=3, max_length=1000),
        hotel_id: Optional[int] = Form(None),
        restaurant_id: Optional[int] = Form(None),
        place_id: Optional[int] = Form(None),
        image_file: Optional[UploadFile] = File(None, description="Optional raw binary photograph attachment stream")
):
    """
    Submits a review for a Hotel, Place, or Restaurant. Supports multi-part local disk photo uploads.
    """
    user_id = current_user.get("id")
    logger.info(f"User ID {user_id} triggered a review transaction process.")

    # 1. Target Validation Check: Enforce targeting exactly one parent profile entity
    targets = [place_id, hotel_id, restaurant_id]
    active_targets = len([t for t in targets if t is not None])

    if active_targets != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A review must target exactly one entity. Provide exactly one: place_id, hotel_id, OR restaurant_id."
        )

    # 2. Defensive Integrity Checks: Confirm targeted entity exists in the active table row index
    if place_id:
        if not db.query(Places).filter(Places.id == place_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Tourist place ID {place_id} does not exist.")

    if hotel_id:
        if not db.query(Hotels).filter(Hotels.id == hotel_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Hotel accommodation ID {hotel_id} does not exist.")

    if restaurant_id:
        if not db.query(Restaurants).filter(Restaurants.id == restaurant_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Restaurant profile ID {restaurant_id} does not exist.")

    # 3. Secure File Upload Pipeline Operations
    final_image_url = None
    if image_file:
        file_ext = os.path.splitext(image_file.filename).lower()
        if file_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type rejected: Only picture formats (.jpg, .jpeg, .png, .webp) are permitted variables."
            )

        # Generate a completely unique filename string to prevent overwriting files on disk
        unique_filename = f"sfd-img-{uuid.uuid4().hex[:10]}{file_ext}"
        file_save_path = os.path.join(UPLOAD_DIR, unique_filename)

        try:
            with open(file_save_path, "wb") as buffer:
                buffer.write(image_file.file.read())
            final_image_url = f"/static/uploads/reviews/{unique_filename}"
        except Exception as e:
            logger.error(f"File writing failure occurred for User {user_id}. Error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server image processor error.")

    # 4. Map values securely into your database model structure
    db_review = Reviews(
        rating=rating,
        comment=comment.strip(),
        image_url=final_image_url,
        user_id=user_id,
        hotel_id=hotel_id,
        restaurant_id=restaurant_id,
        place_id=place_id
    )

    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    logger.info(f"Review ID {db_review.id} successfully generated and saved by user {user_id}.")
    return db_review


@router.get("/place/{place_id}", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
def get_reviews_for_place(place_id: int, db: db_dependency):
    """
    Fetches the public review stream linked to a specific tourist destination.
    """
    return db.query(Reviews).filter(Reviews.place_id == place_id).order_by(Reviews.created_at.desc()).all()


@router.get("/hotel/{hotel_id}", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
def get_reviews_for_hotel(hotel_id: int, db: db_dependency):
    """
    Fetches the public review stream linked to a specific hotel accommodation.
    """
    return db.query(Reviews).filter(Reviews.hotel_id == hotel_id).order_by(Reviews.created_at.desc()).all()


@router.get("/restaurant/{restaurant_id}", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
def get_reviews_for_restaurant(restaurant_id: int, db: db_dependency):
    """
    Fetches the public review stream linked to a specific Pakistani restaurant profile.
    """
    return db.query(Reviews).filter(Reviews.restaurant_id == restaurant_id).order_by(Reviews.created_at.desc()).all()


@router.put("/{review_id}", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
def update_review(review_id: int, review_request: ReviewUpdate, db: db_dependency, current_user: user_dependency):
    """
    Allows a traveler to dynamically alter their own review comment or score.
    """
    user_id = current_user.get("id")
    db_review = db.query(Reviews).filter(Reviews.id == review_id).first()

    if not db_review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review record item not found.")

    # 🔒 Ownership Validation Guard: Ensure a traveler cannot modify another person's submission
    if db_review.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not maintain adequate ownership permissions to update this review."
        )

    update_data = review_request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_review, key, value)

    db.commit()
    db.refresh(db_review)
    return db_review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: db_dependency, current_user: user_dependency):
    """
    Removes a review record permanently from the database cache. Restricted to the original author.
    """
    db_review = db.query(Reviews).filter(Reviews.id == review_id).first()

    if not db_review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review record item not found.")

    # 🔒 Ownership Guard Clause
    if db_review.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not maintain adequate ownership permissions to delete this review."
        )

    db.delete(db_review)
    db.commit()
