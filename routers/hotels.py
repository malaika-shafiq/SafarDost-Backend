import math
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session, joinedload
from database import get_db

# Model and Schema Cross-Imports
from models.hotel import Hotels, HotelRooms, HotelStatusEnum, RoomStatusEnum
from models.image import Images, ImageResourceTypeEnum
from schemas.hotel_schemas import HotelCreate, HotelUpdate, HotelResponse, HotelDetailResponse
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
    Employs 'joinedload' to pre-fetch taxonomy details and filter active items seamlessly.
    """
    # 🏎️ FIXED N+1 QUERY BOTTLENECK: Eager-load relationships and filter for active records
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

    # 6. Optimized Batch Image Processing to completely stop separate inline loops
    hotel_ids = [h.id for h in hotels_list]
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

    # 7. Map payload response safely including relational database text strings
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
            # 🏛️ RELATIONAL INCLUSIONS: Allows the app to render titles natively without extra lookups
            "location_name": hotel.location.name if hotel.location else None,
            "category_name": hotel.category.name if hotel.category else None,
            "images": images_map.get(hotel.id, [])
        })

    return {
        "items": items_response,
        "total": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


# ==========================================
# 2. READ A SINGLE HOTEL PROFILE DETAILS
# ==========================================
@router.get("/{hotel_id}", response_model=HotelDetailResponse, status_code=status.HTTP_200_OK)
def get_hotel_by_id(hotel_id: int, db: db_dependency):
    """
    PUBLIC ACCESSIBLE: Fetch deep profile parameters, nested room details, and photos array list.
    """
    hotel = db.query(Hotels).options(
        joinedload(Hotels.category),
        joinedload(Hotels.location)
    ).filter(Hotels.id == hotel_id).first()

    if not hotel:
        raise HTTPException(status_code=404, detail="Target hotel profile record not found.")

    # Fetch corresponding photos from our polymorphic central table collection
    photos = db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.hotel,
        Images.resource_id == hotel_id
    ).all()

    # Fetch corresponding child inventory rooms linked to this establishment
    rooms = db.query(HotelRooms).filter(HotelRooms.hotel_id == hotel_id).all()

    return {
        "hotel": {
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
            "updated_at": hotel.updated_at
        },
        "images": [img.image_url for img in photos],
        "rooms": rooms
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
        location_id=hotel_request.location_id,
        category_id=hotel_request.category_id,
        creator_id=current_admin.get("id")  # 🏛️ Full audit signature mapping
    )

    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)

    # 2. Iterate and unfold the nested room structures passed inside the single JSON input body
    for room in hotel_request.rooms:
        db_room = HotelRooms(
            hotel_id=db_hotel.id,
            room_type=room.room_type.strip(),
            description=room.description,
            price_per_night=room.price_per_night,
            capacity=room.capacity,
            status=RoomStatusEnum.available
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

    # 🏎️ PERFORMANCE REFACTOR: Uses partial dictionary un-setting mechanics safely
    update_data = hotel_request.model_dump(exclude_unset=True, exclude={"images"})
    for key, value in update_data.items():
        setattr(hotel, key, value)

    # 🏛️ AUDIT TRAIL LOGGING: Actively maps executing admin ID context variables to clear warnings
    hotel.updated_by = current_admin.get("id")

    # Handle structural photo replacements if image arrays are explicitly passed
    if hotel_request.images is not None:
        # First wipe previous image maps to prevent leftover file orphans
        db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.hotel,
            Images.resource_id == hotel_id
        ).delete()

        # Insert fresh image mapping list collections
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
# 5. STAGE 1: SOFT-DELETE A HOTEL (🔒 Admin Only)
# ==========================================
@router.delete("/{hotel_id}", status_code=status.HTTP_200_OK)
def soft_delete_hotel(
        hotel_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Safe stage-1 deletion. Shifts status to 'inactive' to hide the property
    from mobile traveler feeds while preserving historical room booking records and review history.
    """
    hotel = db.query(Hotels).filter(Hotels.id == hotel_id).first()

    # 🏎️ ENUM LOCKDOWN: Performs safe string comparisons against modern system standards
    if not hotel or hotel.status == HotelStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active hotel profile not found or already deactivated."
        )

    # Apply soft-delete switches and record accountability audit trails
    hotel.status = HotelStatusEnum.inactive
    hotel.updated_by = current_admin.get("id")

    db.add(hotel)
    db.commit()
    return {"message": f"Hotel establishment '{hotel.name}' has been safely moved to inactive status."}


# ==========================================
# 6. STAGE 2: PERMANENT PURGE HOTEL (🔒 Admin Only)
# ==========================================
@router.delete("/{hotel_id}/purge", status_code=status.HTTP_200_OK)
def permanently_purge_hotel(
        hotel_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Stage-2 absolute deletion. Permanently wipes the row from disk
    storage, cascading down to drop rooms and strips out related polymorphic image URLs cleanly.
    """
    hotel = db.query(Hotels).filter(Hotels.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Target hotel record not found.")

    # 🔒 TRASH BIN SAFETY GATE: Force them to soft-delete it first before executing a hard purge
    if hotel.status != HotelStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Lock: You must soft-delete this hotel before permanently purging it from storage."
        )

    # 🏛️ AUDIT TRAIL LOGGING: Actively uses the variable payload to clear the PyCharm alert warning!
    print(f"[SECURITY AUDIT] Admin ID {current_admin.get('id')} is executing a permanent hard purge on hotel: {hotel.name}")

    # 1. Clean out nested polymorphic picture rows first to prevent table clutter
    db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.hotel,
        Images.resource_id == hotel_id
    ).delete()

    # 2. Hard-delete the core record item from the physical database table disk (Cascades to rooms)
    db.delete(hotel)
    db.commit()

    return {"message": f"Success. Hotel record '{hotel.name}' and all connected photo assets permanently purged."}
