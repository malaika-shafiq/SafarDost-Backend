import math
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_, desc, asc, func
from sqlalchemy.orm import Session, joinedload
from database import get_db

# Model and Schema Cross-Imports
from models.transport import Transports, TransportStatusEnum, TransportRentalModeEnum
from models.image import Images, ImageResourceTypeEnum
from models.review import Reviews, ReviewStatusEnum
from models.user import Users
from schemas.transport_schemas import TransportCreate, TransportUpdate, TransportResponse, TransportDetailResponse
from utils.auth_utils import get_current_admin  # 🔒 Security Gate Dependency

router = APIRouter(prefix="/transports", tags=["Transport Fleet Fleet Management"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_current_admin)]


# ==========================================
# 1. READ ALL TRANSPORTS (Optimized Pagination, Search & Route Filters)
# ==========================================
@router.get("", status_code=status.HTTP_200_OK)
def get_all_transports_paginated(
        db: db_dependency,
        page: int = Query(1, ge=1, description="Page number starting from 1"),
        limit: int = Query(10, ge=1, le=50, description="Items per page"),
        search: Optional[str] = Query(None, description="Search vehicle fleet by model type description"),
        from_location: Optional[str] = Query(None, description="Filter fleet vehicles by origin starting point"),
        to_location: Optional[str] = Query(None, description="Filter fleet vehicles by target destination point")
):
    """
    PUBLIC ACCESSIBLE: Browse and discover available transit options across Northern paths.
    Employs an optimized batch image map processor to completely eliminate inline N+1 loop penalties.
    """
    query = db.query(Transports).filter(Transports.status == TransportStatusEnum.active)

    if search:
        query = query.filter(Transports.transport_type.ilike(f"%{search}%"))
    if from_location:
        query = query.filter(Transports.from_location.ilike(f"%{from_location}%"))
    if to_location:
        query = query.filter(Transports.to_location.ilike(f"%{to_location}%"))

    query = query.order_by(desc(Transports.created_at))
    total_items = query.count()

    offset = (page - 1) * limit
    transports_list = query.offset(offset).limit(limit).all()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0

    transport_ids = [t.id for t in transports_list]
    images_map = {}
    if transport_ids:
        all_photos = db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.transport,
            Images.resource_id.in_(transport_ids)
        ).all()
        for img in all_photos:
            if img.resource_id not in images_map:
                images_map[img.resource_id] = []
            images_map[img.resource_id].append(img.image_url)

    items_response = []
    for vehicle in transports_list:
        items_response.append({
            "id": vehicle.id,
            "transport_type": vehicle.transport_type,
            "from_location": vehicle.from_location,
            "to_location": vehicle.to_location,
            "departure_time": vehicle.departure_time,
            "arrival_time": vehicle.arrival_time,
            "price": vehicle.price,
            "capacity": vehicle.capacity,
            "rental_mode": vehicle.rental_mode,
            "available_seats": vehicle.available_seats,
            "status": vehicle.status,
            "location_id": vehicle.location_id,
            "creator_id": vehicle.creator_id,
            "updated_by": vehicle.updated_by,
            "created_at": vehicle.created_at,
            "updated_at": vehicle.updated_at,
            "images": images_map.get(vehicle.id, [])
        })

    return {
        "items": items_response,
        "total": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


# ==========================================
# 2. READ A SINGLE VEHICLE RENTAL PROFILE DETAILS (With Polymorphic Review Links)
# ==========================================
@router.get("/{transport_id}", response_model=TransportDetailResponse, status_code=status.HTTP_200_OK)
def get_transport_by_id(transport_id: int, db: db_dependency):
    """
    PUBLIC ACCESSIBLE: Fetch deep operational constraints, vehicle images, and nested traveler feedback arrays.
    Dynamically computes real-time rating telemetry using eager relational loading rules.
    """
    # 🏎️ EAGER LOADS REVIEWS: Uses joinedload parameters to pull review and reviewer user references in 1 operation
    vehicle = db.query(Transports).options(
        joinedload(Transports.reviews).joinedload(Reviews.user)
    ).filter(Transports.id == transport_id).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Target fleet transport profile record not found.")

    photos = db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.transport,
        Images.resource_id == transport_id
    ).all()

    # 🧠 ON-THE-FLY AGGREGATION ALGORITHM: Rounds scores cleanly without storage schema redundancy costs
    avg_score = db.query(func.avg(Reviews.rating)).filter(
        Reviews.transport_id == transport_id,
        Reviews.status == ReviewStatusEnum.active
    ).scalar()

    final_rating = round(avg_score, 1) if avg_score else 0.0

    compiled_reviews = []
    for r in vehicle.reviews:
        if r.status == ReviewStatusEnum.active:
            compiled_reviews.append({
                "id": r.id,
                "rating": r.rating,
                "comment": r.comment,
                "reviewer_name": r.user.name if r.user else "Anonymous Traveler",
                "created_at": r.created_at
            })

    return {
        "transport": vehicle,
        "images": [img.image_url for img in photos],
        "reviews": compiled_reviews,
        "average_rating": final_rating,
        "total_reviews_count": len(compiled_reviews)
    }

# ==========================================
# 3. CREATE A TRANSPORT FLEET ASSET (🔒 Admin Account Gate Only)
# ==========================================
@router.post("", response_model=TransportResponse, status_code=status.HTTP_201_CREATED)
def create_new_transport_asset(
        transport_request: TransportCreate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Registers a new fleet vehicle profile under direct administrative accountability tracking records.
    Unfolds request vehicle image URL arrays smoothly into the central polymorphic storage engine.
    """
    db_transport = Transports(
        transport_type=transport_request.transport_type.strip(),
        from_location=transport_request.from_location.strip(),
        to_location=transport_request.to_location.strip(),
        departure_time=transport_request.departure_time.strip(),
        arrival_time=transport_request.arrival_time.strip(),
        price=transport_request.price,
        capacity=transport_request.capacity,
        rental_mode=transport_request.rental_mode,
        available_seats=transport_request.capacity,  # On creation, seats remaining matches total capacity
        location_id=transport_request.location_id,
        creator_id=current_admin.get("id"),
        status=TransportStatusEnum.active
    )

    db.add(db_transport)
    db.commit()
    db.refresh(db_transport)

    for url in transport_request.images:
        db_image = Images(
            image_url=url,
            resource_type=ImageResourceTypeEnum.transport,
            resource_id=db_transport.id,
            creator_id=current_admin.get("id")
        )
        db.add(db_image)

    db.commit()
    return db_transport


# ==========================================
# 4. UPDATE AN EXISTING VEHICLE PROFILE (🔒 Admin Account Gate Only)
# ==========================================
@router.put("/{transport_id}", response_model=TransportResponse, status_code=status.HTTP_200_OK)
def update_transport_asset(
        transport_id: int,
        transport_request: TransportUpdate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Modify existing fleet configuration parameters and trace structural updates safely.
    """
    vehicle = db.query(Transports).filter(Transports.id == transport_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Target transport fleet profile record not found.")

    update_data = transport_request.model_dump(exclude_unset=True, exclude={"images"})
    for key, value in update_data.items():
        setattr(vehicle, key, value)

    if "capacity" in update_data:
        vehicle.available_seats = transport_request.capacity

    vehicle.updated_by = current_admin.get("id")

    if transport_request.images is not None:
        db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.transport,
            Images.resource_id == transport_id
        ).delete()

        for url in transport_request.images:
            db_image = Images(
                image_url=url,
                resource_type=ImageResourceTypeEnum.transport,
                resource_id=transport_id,
                creator_id=current_admin.get("id")
            )
            db.add(db_image)

    db.commit()
    db.refresh(vehicle)
    return vehicle


# ==========================================
# 5. STAGE 1: SOFT-DELETE A VEHICLE (🔒 Admin Only Gate)
# ==========================================
@router.delete("/{transport_id}", status_code=status.HTTP_200_OK)
def soft_delete_transport(
        transport_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Safe stage-1 deletion. Shifts status to 'inactive' to mask it from
    traveler feeds while preserving underlying reservation data histories.
    """
    vehicle = db.query(Transports).filter(Transports.id == transport_id).first()
    if not vehicle or vehicle.status == TransportStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active fleet asset profile not found or already deactivated."
        )

    vehicle.status = TransportStatusEnum.inactive
    vehicle.updated_by = current_admin.get("id")

    db.add(vehicle)
    db.commit()
    return {"message": f"Transport asset model '{vehicle.transport_type}' moved to inactive status."}


# ==========================================
# 6. STAGE 2: PERMANENT PURGE VEHICLE (🔒 Admin Only Gate)
# ==========================================
@router.delete("/{transport_id}/purge", status_code=status.HTTP_200_OK)
def permanently_purge_transport(
        transport_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Stage-2 absolute deletion. Permanently wipes the row from physical disk table storage
    and drops intermediate polymorphic photo url paths cleanly from the database ecosystem.
    """
    vehicle = db.query(Transports).filter(Transports.id == transport_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Target transport fleet record not found.")

    if vehicle.status != TransportStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Lock: You must soft-delete this transport profile before permanently purging it from memory."
        )

    print(f"[SECURITY PURGE AUDIT] Admin ID {current_admin.get('id')} is hard purging vehicle asset: {vehicle.transport_type}")

    db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.transport,
        Images.resource_id == transport_id
    ).delete()

    db.delete(vehicle)
    db.commit()

    return {"message": f"Success. Transport fleet asset '{vehicle.transport_type}' permanently wiped from disk."}
