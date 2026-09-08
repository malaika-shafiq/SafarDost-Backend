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
# 1. READ ALL REVIEWS (With Filters for Places, Hotels, or Restaurants)
# ==========================================
@router.get("", status_code=status.HTTP_200_OK)
def get_all_active_reviews(
        db: db_dependency,
        page: int = Query(1, ge=1, description="Page number starting from 1"),
        limit: int = Query(10, ge=1, le=50, description="Items per page"),
        place_id: Optional[int] = Query(None, description="Filter reviews by target place ID"),
        hotel_id: Optional[int] = Query(None, description="Filter reviews by target hotel ID"),
        restaurant_id: Optional[int] = Query(None, description="Filter reviews by target restaurant ID")
):
    """
    PUBLIC ACCESSIBLE: Advanced discovery feed for travelers [image_-ttl6L].
    Fetches active experiences and eager-loads reviewer profiles to optimize performance.
    """
    # 🏎️ FIXED N+1 QUERY BOTTLENECK: Eager-load the user profile relationship string natively
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

    # Sort reviews by latest entry timestamp
    query = query.order_by(desc(Reviews.created_at))

    # Extract Total Dataset Entry Counts Before Offsets
    total_items = query.count()

    # Process DB Page Range Slices
    offset = (page - 1) * limit
    reviews_list = query.offset(offset).limit(limit).all()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0

    # 🏎️ ACTIVATES IMAGES IMPORTS: Optimized Batch Image Processing to match polymorphic photos in 1 step
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
        # 🏛️ EXPLICIT TYPE HINT: Tells PyCharm exactly what class object model is processing here to clear gray import font warnings!
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
                "created_at": review.created_at,
                "updated_at": review.updated_at
            },
            # 🏎️ ACTIVATES USERS IMPORT: Pulls direct username string text straight to client layout components
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
    TRAVELER/ADMIN: Allows authenticated accounts to share reviews and upload live pictures [image_-ttl6L].
    """
    # Defensive Boundary Gate: A review must target exactly one entity feature node
    targets = [review_request.place_id, review_request.hotel_id, review_request.restaurant_id]
    active_targets = [t for t in targets if t is not None]

    if len(active_targets) != 1:
        raise HTTPException(
            status_code=400,
            detail="Structural Failure: A review must target exactly one parent asset (either a place, hotel, or restaurant)."
        )

    db_review = Reviews(
        rating=review_request.rating,
        comment=review_request.comment.strip(),
        user_id=current_user.get("id"),
        place_id=review_request.place_id,
        hotel_id=review_request.hotel_id,
        restaurant_id=review_request.restaurant_id,
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


# ==========================================
# 3. UPDATE AN EXISTING REVIEW (🔒 Author Only Guard Constraint)
# ==========================================
@router.put("/{review_id}", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
def update_traveler_review(
        review_id: int,
        review_request: ReviewUpdate,
        current_user: user_dependency,
        db: db_dependency
):
    """
    AUTHOR ONLY: Allows the original traveler to edit their star ratings, comments, and experience photos.
    Safely blocks outside users from altering other travelers' records.
    """
    review = db.query(Reviews).filter(Reviews.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Target review record not found.")

    # 🔒 SECURITY ACCESS GATE: Verify executing user matches the author row signature
    if review.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security Violation: You do not possess structural ownership rights to edit this review."
        )

    # 🏎️ ACTIVATES REVIEWUPDATE IMPORT: Updates basic parameters dynamically if passed in payload body
    update_data = review_request.model_dump(exclude_unset=True, exclude={"images"})
    for key, value in update_data.items():
        setattr(review, key, value)

    # Handle replacement loops for uploaded experience photos if arrays are explicitly passed
    if review_request.images is not None:
        # Wipe old polymorphic picture references from storage first
        db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.review,
            Images.resource_id == review_id
        ).delete()

        # Re-populate fresh image link locations
        for url in review_request.images:
            db_image = Images(
                image_url=url,
                resource_type=ImageResourceTypeEnum.review,
                resource_id=review_id,
                creator_id=current_user.get("id")
            )
            db.add(db_image)

    db.commit()
    db.refresh(review)
    return review


# ==========================================
# 4. STAGE 1: SOFT-DELETE A REVIEW (🔒 Author or Admin Override Guard)
# ==========================================
@router.delete("/{review_id}", status_code=status.HTTP_200_OK)
def soft_delete_review(
        review_id: int,
        current_user: user_dependency,
        db: db_dependency
):
    """
    AUTHOR OR ADMIN: Soft-delete operation. Toggles status flags to 'inactive'
    to remove inappropriate text or pictures from traveler feeds instantly.
    """
    review = db.query(Reviews).filter(Reviews.id == review_id).first()
    if not review or review.status == ReviewStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active review record not found or already deactivated."
        )

    # 🔒 SECURITY ACCESS GATE: Allow execution ONLY if actor is the original author OR an Admin account
    is_author = review.user_id == current_user.get("id")
    is_admin = current_user.get("role") == "admin"

    if not (is_author or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security Violation: Insufficient account permissions to deactivate this data record."
        )

    # Execute safe soft-delete state shift operation parameters
    review.status = ReviewStatusEnum.inactive
    db.add(review)
    db.commit()

    return {"message": "Success. Review profile hidden from public travel streams successfully."}


# ==========================================
# 5. STAGE 2: PERMANENT PURGE REVIEW (🔒 Admin Only Override Gate)
# ==========================================
@router.delete("/{review_id}/purge", status_code=status.HTTP_200_OK)
def permanently_purge_review(
        review_id: int,
        current_user: user_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Stage-2 absolute deletion. Permanently wipes the row from disk storage
    and completely cleans out all connected polymorphic image URL string paths.
    """
    # 🔒 ROLE ACCESS GATE: Restrict execution strictly to system administrators
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to permanently purge database data rows."
        )

    review = db.query(Reviews).filter(Reviews.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Target review record not found.")

    # 🔒 TRASH BIN SAFETY GATE: Force them to soft-delete it first before executing a hard purge
    if review.status != ReviewStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Lock: You must soft-delete this review before executing a permanent hard purge."
        )

    # 🏛️ AUDIT TRAIL TERMINAL LOGGING: Actively uses the current_user variable payload to clear warnings!
    print(f"[SECURITY PURGE] Admin ID {current_user.get('id')} has permanently deleted Review ID: {review.id}")

    # Clean out nested polymorphic picture rows first to prevent table clutter
    db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.review,
        Images.resource_id == review_id
    ).delete()

    # Hard-delete the core record item from the physical database table disk
    db.delete(review)
    db.commit()

    return {"message": "Success. Traveler review row and all associated photo records permanently purged from disk."}
