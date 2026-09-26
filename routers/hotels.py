import math
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_, desc, asc, func
from sqlalchemy.orm import Session, joinedload
from database import get_db

# Model and Schema Cross-Imports
from models.hotel import Hotels, HotelRooms, HotelStatusEnum
from models.image import Images, ImageResourceTypeEnum
from models.review import Reviews, ReviewStatusEnum  # 👈 Activated your core Review models here!
from schemas.hotel_schemas import (
    HotelCreate,
    HotelUpdate,
    HotelResponse,
    HotelDetailResponse,
    RoomQuantityUpdate,
    RoomResponse
)
from utils.auth_utils import get_current_admin  # 🔒 Security Gate Dependency

router = APIRouter(prefix="/hotels", tags=["Hotels & Inventory Management"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_current_admin)]


# ==========================================
# 1. READ ALL HOTELS (Optimized Pagination, Search & Eager Loading)
# ==========================================
@router.get("", status_code=status.HTTP_200_OK)
def get_all_hotels_paginated(
        db: db_dependency,
        page: int = Query(1, ge=1, description="Page number starting from 1"),
        limit: int = Query(10, ge=1, le=50, description="Items per page"),
        search: Optional[str] = Query(None, description="Search across hotel name, facilities or details"),
        location_id: Optional[int] = Query(None, description="Filter hotels by master location ID"),
        category_id: Optional[int] = Query(None, description="Filter hotels by master category ID"),
        sort_by: str = Query("id", description="Field to sort by (id, name, created_at)"),
        order: str = Query("desc", description="Sort execution order (asc or desc)")
):
    """
    PUBLIC ACCESSIBLE: Advanced discovery endpoint for mobile travelers.
    Employs optimized batch image and batch room loaders to completely eliminate inline N+1 loop penalties.
    """
    # FIXED N+1 QUERY BOTTLENECK: Eager-load taxonomy tables natively
    query = db.query(Hotels).options(
        joinedload(Hotels.category),
        joinedload(Hotels.location)
    ).filter(Hotels.status == HotelStatusEnum.active)

    # 1. Apply Dynamic Search Text Bounds
    if search:
        query = query.filter(
            or_(
                Hotels.name.ilike(f"%{search}%"),
                Hotels.facilities.ilike(f"%{search}%"),
                Hotels.description.ilike(f"%{search}%")
            )
        )

    # 2. Apply Optional Foreign Key Segment Filters
    if location_id:
        query = query.filter(Hotels.location_id == location_id)
    if category_id:
        query = query.filter(Hotels.category_id == category_id)

    # 3. Process Dynamic Sorting Constraints
    sort_column = getattr(Hotels, sort_by, Hotels.id)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # 4. Extract Total Dataset Entry Counts Before Offsets
    total_items = query.count()

    # 5. Process DB Page Range Slices
    offset = (page - 1) * limit
    hotels_list = query.offset(offset).limit(limit).all()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0

    # Extract all active IDs in the current page batch
    hotel_ids = [h.id for h in hotels_list]

    # 6. Optimized Batch Image Processing
    images_map = {}
    if hotel_ids:
        all_photos = db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.hotel,
            Images.resource_id.in_(hotel_ids)
        ).all()
        for img in all_photos:
            if img.resource_id not in images_map:
                images_map[img.resource_id] = []
            images_map[img.resource_id].append(img.image_url)

    # 🚀 7. [NEW] OPTIMIZED BATCH ROOM SUPPLIES PROCESSOR MAP (Eliminates N+1 loop penalties) [INDEX: 1.1.2]
    rooms_map = {}
    if hotel_ids:
        all_rooms = db.query(HotelRooms).filter(HotelRooms.hotel_id.in_(hotel_ids)).all()
        for rm in all_rooms:
            if rm.hotel_id not in rooms_map:
                rooms_map[rm.hotel_id] = []
            rooms_map[rm.hotel_id].append({
                "id": rm.id,
                "room_type": rm.room_type,
                "description": rm.description,
                "price_per_night": rm.price_per_night,
                "capacity": rm.capacity,
                "quantity": rm.quantity
            })

    # 8. Map payload response safely including relational database text strings and room list blocks [INDEX: 1.1.2]
    items_response = []
    for hotel in hotels_list:
        items_response.append({
            "id": hotel.id,
            "name": hotel.name,
            "description": hotel.description,
            "contact_information": hotel.contact_information,
            "facilities": hotel.facilities,
            "status": hotel.status,
            "location_id": hotel.location_id,
            "category_id": hotel.category_id,
            "creator_id": hotel.creator_id,
            "updated_by": hotel.updated_by,
            "created_at": hotel.created_at,
            "updated_at": hotel.updated_at,
            "location_name": hotel.location.name if hotel.location else None,
            "category_name": hotel.category.name if hotel.category else None,
            "images": images_map.get(hotel.id, []),
            "rooms": rooms_map.get(hotel.id, [])  # 🚀 NESTED ROOM FEED BLOCKS FULLY ATTACHED
        })

    return {
        "items": items_response,
        "total": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }



# ==========================================
# 2. READ A SINGLE HOTEL PROFILE DETAILS (With Live Review Aggregations)
# ==========================================
@router.get("/{hotel_id}", response_model=HotelDetailResponse, status_code=status.HTTP_200_OK)
def get_hotel_by_id(hotel_id: int, db: db_dependency):
    """
    PUBLIC ACCESSIBLE: Fetch deep profile parameters, nested room stock types, and traveler feedback arrays.
    Dynamically pre-fetches and aggregates review star telemetry using eager relational loading rules.
    """
    # 🏎️ EAGER LOADS REVIEWS: Uses joinedload parameters to pull review and reviewer user references in 1 operation
    hotel = db.query(Hotels).options(
        joinedload(Hotels.category),
        joinedload(Hotels.location),
        joinedload(Hotels.reviews).joinedload(Reviews.user)
    ).filter(Hotels.id == hotel_id).first()

    if not hotel:
        raise HTTPException(status_code=404, detail="Target hotel profile record not found.")

    # Fetch corresponding photos from our polymorphic central table collection
    photos = db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.hotel,
        Images.resource_id == hotel_id
    ).all()

    # Fetch corresponding child inventory rooms types linked to this establishment
    rooms = db.query(HotelRooms).filter(HotelRooms.hotel_id == hotel_id).all()

    # 🧠 ON-THE-FLY AGGREGATION ALGORITHM: Rounds scores cleanly without storage schema redundancy costs
    avg_score = db.query(func.avg(Reviews.rating)).filter(
        Reviews.hotel_id == hotel_id,
        Reviews.status == ReviewStatusEnum.active
    ).scalar()

    final_rating = round(avg_score, 1) if avg_score else 0.0

    compiled_reviews = []
    for r in hotel.reviews:
        if r.status == ReviewStatusEnum.active:
            compiled_reviews.append({
                "id": r.id,
                "rating": r.rating,
                "comment": r.comment,
                "reviewer_name": r.user.name if r.user else "Anonymous Traveler",
                "created_at": r.created_at
            })

    return {
        "hotel": hotel,
        "images": [img.image_url for img in photos],
        "rooms": rooms,
        "reviews": compiled_reviews,  # 🚀 Delivered natively to client mobile layouts
        "average_rating": final_rating,  # 🚀 Populates dynamic stars on the screen components
        "total_reviews_count": len(compiled_reviews)
    }

# ==========================================
# 3. CREATE A HOTEL (🔒 Admin Account Gate Only)
# ==========================================
@router.post("", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
def create_new_hotel(
        hotel_request: HotelCreate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Inserts a new hospitality establishment and loops its room structure inventory natively.
    Unfolds request image array pointers smoothly into the central polymorphic engine.
    """
    clean_name = hotel_request.name.strip()
    existing_spot = db.query(Hotels).filter(
        Hotels.name.ilike(clean_name),
        Hotels.location_id == hotel_request.location_id
    ).first()

    if existing_spot:
        raise HTTPException(
            status_code=400,
            detail=f"A hotel establishment named '{clean_name}' already exists inside this regional destination node."
        )

    # 1. Base property fields creation mapping
    db_hotel = Hotels(
        name=clean_name,
        description=hotel_request.description,
        contact_information=hotel_request.contact_information.strip(),
        facilities=hotel_request.facilities,
        base_price=hotel_request.base_price,
        location_id=hotel_request.location_id,
        category_id=hotel_request.category_id,
        creator_id=current_admin.get("id")
    )

    db_hotel.rooms = []  # Explicitly initialize as an empty relationship list block

    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)

    # 2. Iterate and unfold the nested room category structures containing bulk quantities
    for room in hotel_request.rooms:
        db_room = HotelRooms(
            hotel_id=db_hotel.id,
            room_type=room.room_type.strip(),
            description=room.description,
            price_per_night=room.price_per_night,
            capacity=room.capacity,
            quantity=room.quantity
        )
        db.add(db_room)

    # 3. Automatically unrolls incoming string urls directly into our central media repository table
    for url in hotel_request.images:
        db_image = Images(
            image_url=url,
            resource_type=ImageResourceTypeEnum.hotel,
            resource_id=db_hotel.id,
            creator_id=current_admin.get("id")
        )
        db.add(db_image)

    db.commit()
    db.refresh(db_hotel)
    return db_hotel


# ==========================================
# 4. UPDATE AN EXISTING HOTEL (🔒 Admin Account Gate Only)
# ==========================================
@router.put("/{hotel_id}", response_model=HotelResponse, status_code=status.HTTP_200_OK)
def update_hotel(
        hotel_id: int,
        hotel_request: HotelUpdate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Modify existing hotel property fields and track changes dynamically.
    Safely ignores unset fields to prevent accidental layout overrides.
    """
    hotel = db.query(Hotels).filter(Hotels.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Target hotel profile record not found.")

    # Uses partial dictionary un-setting mechanics safely
    update_data = hotel_request.model_dump(exclude_unset=True, exclude={"images"})
    for key, value in update_data.items():
        setattr(hotel, key, value)

    hotel.updated_by = current_admin.get("id")

    # Handle structural photo replacements if image arrays are explicitly passed
    if hotel_request.images is not None:
        db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.hotel,
            Images.resource_id == hotel_id
        ).delete()

        for url in hotel_request.images:
            db_image = Images(
                image_url=url,
                resource_type=ImageResourceTypeEnum.hotel,
                resource_id=hotel_id,
                creator_id=current_admin.get("id")
            )
            db.add(db_image)

    db.commit()
    db.refresh(hotel)
    return hotel


# ==========================================
# 5. MODIFY ROOM QUANTITY (🔒 Admin Only)
# ==========================================
@router.put("/rooms/{room_id}/quantity", response_model=RoomResponse, status_code=status.HTTP_200_OK)
def update_room_quantity(
        room_id: int,
        quantity_payload: RoomQuantityUpdate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Simple, high-efficiency endpoint to adjust a room type's global baseline stock capacity count.
    """
    room = db.query(HotelRooms).filter(HotelRooms.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Target room inventory record not found.")

    room.quantity = quantity_payload.quantity

    parent_hotel = db.query(Hotels).filter(Hotels.id == room.hotel_id).first()
    if parent_hotel:
        parent_hotel.updated_by = current_admin.get("id")

    db.commit()
    db.refresh(room)
    return room


# ==========================================
# 6. STAGE 1: SOFT-DELETE A HOTEL (🔒 Admin Only)
# ==========================================
@router.delete("/{hotel_id}", status_code=status.HTTP_200_OK)
def soft_delete_hotel(
        hotel_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Safe stage-1 deactivation. Shifts status to 'inactive' to hide the property
    from mobile traveler feeds while preserving historical room booking records and review history.
    """
    hotel = db.query(Hotels).filter(Hotels.id == hotel_id).first()

    if not hotel or hotel.status == HotelStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active hotel profile not found or already deactivated."
        )

    hotel.status = HotelStatusEnum.inactive
    hotel.updated_by = current_admin.get("id")

    db.add(hotel)
    db.commit()
    return {"message": f"Hotel establishment '{hotel.name}' has been safely moved to inactive status."}


# ==========================================
# 7. STAGE 2: PERMANENT PURGE HOTEL (🔒 Admin Only)
# ==========================================
@router.delete("/{hotel_id}/purge", status_code=status.HTTP_200_OK)
def permanently_purge_hotel(
        hotel_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Stage-2 absolute deletion. Permanently wipes rows from physical disk,
    cascading down to clean rooms and strips out related polymorphic image URLs cleanly.
    """
    hotel = db.query(Hotels).filter(Hotels.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Target hotel record not found.")

    if hotel.status != HotelStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Lock: You must soft-delete this hotel before permanently purging it from storage."
        )

    print(f"[SECURITY AUDIT] Admin ID {current_admin.get('id')} is executing a permanent hard purge on hotel: {hotel.name}")

    # 1. Clean out nested polymorphic picture rows first
    db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.hotel,
        Images.resource_id == hotel_id
    ).delete()

    # 2. Hard-delete core item (Cascades down to drop child hotel_rooms rows and nested reviews cleanly)
    db.delete(hotel)
    db.commit()

    return {"message": f"Success. Hotel record '{hotel.name}' and all connected photo assets permanently purged."}
