import math
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session, joinedload
from database import get_db

# Model and Schema Cross-Imports — ALL ACTIVATED
from models.review import Reviews, ReviewStatusEnum
from models.image import Images, ImageResourceTypeEnum
from models.user import Users
from schemas.review_schemas import ReviewCreate, ReviewUpdate, ReviewResponse
from utils.auth_utils import get_current_user  # 🔒 Security Gate Dependency

router = APIRouter(prefix="/reviews", tags=["Reviews & Experiences Module"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# ==========================================
# 1. READ ALL REVIEWS (With Filters for Places, Hotels, Restaurants, or Transports)
# ==========================================
@router.get("", status_code=status.HTTP_200_OK)
def get_all_active_reviews(
        db: db_dependency,
        page: int = Query(1, ge=1, description="Page number starting from 1"),
        limit: int = Query(10, ge=1, le=50, description="Items per page"),
        place_id: Optional[int] = Query(None, description="Filter reviews by target place ID"),
        hotel_id: Optional[int] = Query(None, description="Filter reviews by target hotel ID"),
        restaurant_id: Optional[int] = Query(None, description="Filter reviews by target restaurant ID"),
        transport_id: Optional[int] = Query(None, description="Filter reviews by target transport vehicle ID") # 👈 EXTENDED FEED FILTER Query
):
    """
    PUBLIC ACCESSIBLE: Advanced discovery feed for travelers.
    Fetches active experiences and eager-loads reviewer profiles to optimize performance.
    """
    query = db.query(Reviews).options(
        joinedload(Reviews.user)
    ).filter(Reviews.status == ReviewStatusEnum.active)

    # Apply Relational Context Filters
    if place_id:
        query = query.filter(Reviews.place_id == place_id)
    if hotel_id:
        query = query.filter(Reviews.hotel_id == hotel_id)
    if restaurant_id:
        query = query.filter(Reviews.restaurant_id == restaurant_id)
    if transport_id:
        query = query.filter(Reviews.transport_id == transport_id)  # 👈 LIVE TRANSPORT MATCH ROUTE

    # Sort reviews by latest entry timestamp
    query = query.order_by(desc(Reviews.created_at))

    # Extract Total Dataset Entry Counts Before Offsets
    total_items = query.count()

    # Process DB Page Range Slices
    offset = (page - 1) * limit
    reviews_list = query.offset(offset).limit(limit).all()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0

    # Optimized Batch Image Processing to match polymorphic photos in 1 step
    review_ids = [r.id for r in reviews_list]
    images_map = {}
    if review_ids:
        all_photos = db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.review,
            Images.resource_id.in_(review_ids)
        ).all()
        for img in all_photos:
            if img.resource_id not in images_map:
                images_map[img.resource_id] = []
            images_map[img.resource_id].append(img.image_url)

    # Package structured response array matching mobile screen expectations
    items_response = []
    for review in reviews_list:
        reviewer: Users = review.user
        items_response.append({
            "review": {
                "id": review.id,
                "rating": review.rating,
                "comment": review.comment,
                "status": review.status,
                "user_id": review.user_id,
                "place_id": review.place_id,
                "hotel_id": review.hotel_id,
                "restaurant_id": review.restaurant_id,
                "transport_id": review.transport_id,  # 👈 RETURNS NESTED VEHICLE RELATIONS IN FEEDS
                "created_at": review.created_at,
                "updated_at": review.updated_at
            },
            "reviewer_name": reviewer.name if reviewer else "Anonymous Traveler",
            "images": images_map.get(review.id, [])
        })

    return {
        "items": items_response,
        "total": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


# ==========================================
# 2. CREATE A REVIEW & EXPERIENCE (🔒 Authenticated Travelers/Admins)
# ==========================================
@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def write_new_traveler_review(
        review_request: ReviewCreate,
        current_user: user_dependency,
        db: db_dependency
):
    """
    TRAVELER/ADMIN: Allows authenticated accounts to share reviews and upload live pictures.
    Strictly guarantees that a review links to exactly one system entity module.
    """
    # Defensive Boundary Gate: A review must target exactly one entity feature node across our 4 modules
    targets = [
        review_request.place_id,
        review_request.hotel_id,
        review_request.restaurant_id,
        review_request.transport_id  # 👈 INTEGRATED INTO EXCLUSIVE BOUNDARY GATE CODES
    ]
    active_targets = [t for t in targets if t is not None]

    if len(active_targets) != 1:
        raise HTTPException(
            status_code=400,
            detail="Structural Failure: A review must target exactly one parent asset (either a place, hotel, restaurant, or transport)."
        )

    db_review = Reviews(
        rating=review_request.rating,
        comment=review_request.comment.strip(),
        user_id=current_user.get("id"),
        place_id=review_request.place_id,
        hotel_id=review_request.hotel_id,
        restaurant_id=review_request.restaurant_id,
        transport_id=review_request.transport_id,  # 🚀 COMMITS VEHICLE REFERENCE VALUE TO PERSISTENT STORAGE ROWS
        status=ReviewStatusEnum.active
    )

    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    if review_request.images:
        for url in review_request.images:
            db_image = Images(
                image_url=url,
                resource_type=ImageResourceTypeEnum.review,
                resource_id=db_review.id,
                creator_id=current_user.get("id")
            )
            db.add(db_image)
        db.commit()

    return db_review
