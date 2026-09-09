import math
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session
from database import get_db

# Model and Schema Cross-Imports
from models.transport import Transports, TransportStatusEnum
from models.image import Images, ImageResourceTypeEnum
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
    PUBLIC ACCESSIBLE: Browse and discover available transit options across specific regional routes.
    Employs an optimized batch image map processor to completely eliminate inline N+1 loop penalties.
    """
    query = db.query(Transports).filter(Transports.status == TransportStatusEnum.active)

    # 1. Apply Dynamic Fleet Search Text Bounds
    if search:
        query = query.filter(Transports.transport_type.ilike(f"%{search}%"))

    # 2. Apply Strict Route Filtering parameters
    if from_location:
        query = query.filter(Transports.from_location.ilike(f"%{from_location}%"))
    if to_location:
        query = query.filter(Transports.to_location.ilike(f"%{to_location}%"))

    # Sort catalog results chronologically by latest entry timestamp
    query = query.order_by(desc(Transports.created_at))

    # 3. Extract Total Dataset Entry Counts Before Offsets
    total_items = query.count()

    # 4. Process DB Page Range Slices
    offset = (page - 1) * limit
    transports_list = query.offset(offset).limit(limit).all()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0

    # 5. Optimized Batch Image Processing to match polymorphic vehicle cover links in 1 step
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

    # 6. Map payload response array matching client mobile screen layout requirements
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
# 2. READ A SINGLE VEHICLE RENTAL PROFILE DETAILS
# ==========================================
@router.get("/{transport_id}", response_model=TransportDetailResponse, status_code=status.HTTP_200_OK)
def get_transport_by_id(transport_id: int, db: db_dependency):
    """
    PUBLIC ACCESSIBLE: Fetch deep operational constraints, timings, and picture URL paths for a transit profile node.
    """
    vehicle = db.query(Transports).filter(Transports.id == transport_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Target fleet transport profile record not found.")

    photos = db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.transport,
        Images.resource_id == transport_id
    ).all()

    return {
        "transport": vehicle,
        "images": [img.image_url for img in photos]
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
        location_id=transport_request.location_id,
        creator_id=current_admin.get("id"),  # 🏛️ Full audit signature mapping
        status=TransportStatusEnum.active
    )

    db.add(db_transport)
    db.commit()
    db.refresh(db_transport)

    # Automatically unrolls vehicle covers into our central polymorphic repository table
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

    # 🏎️ PERFORMANCE REFACTOR: Uses partial dictionary un-setting mechanics safely
    update_data = transport_request.model_dump(exclude_unset=True, exclude={"images"})
    for key, value in update_data.items():
        setattr(vehicle, key, value)

    # Record accountability modifier logs mapping the current administrator's account ID
    vehicle.updated_by = current_admin.get("id")

    # Handle structural photo replacements if image arrays are explicitly passed
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
    ADMIN ONLY: Safe stage-1 deletion [image_Ay70D1]. Shifts status to 'inactive' to mask it from
    traveler feeds while preserving underlying reservation data histories.
    """
    vehicle = db.query(Transports).filter(Transports.id == transport_id).first()
    if not vehicle or vehicle.status == TransportStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active fleet asset profile not found or already deactivated."
        )

    # Shift operational status variables and track accountability audit trails
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
    ADMIN ONLY: Stage-2 absolute deletion [image_Ay70D1]. Permanently wipes the row from physical disk table storage
    and drops intermediate polymorphic photo url paths cleanly from the database ecosystem.
    """
    vehicle = db.query(Transports).filter(Transports.id == transport_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Target transport fleet record not found.")

    # 🔒 TRASH BIN SAFETY GATE: Force them to soft-delete it first before executing a hard purge
    if vehicle.status != TransportStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Lock: You must soft-delete this transport profile before permanently purging it from memory."
        )

    # 🏛️ AUDIT LOGGING OVERRIDES: Print output utilizes variables natively to clear PyCharm gray alerts
    print(f"[SECURITY PURGE AUDIT] Admin ID {current_admin.get('id')} is hard purging vehicle asset: {vehicle.transport_type}")

    # 1. Clear out nested polymorphic vehicle picture asset references from storage first
    db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.transport,
        Images.resource_id == transport_id
    ).delete()

    # 2. Hard-delete the core record item from the physical database table disk
    db.delete(vehicle)
    db.commit()

    return {"message": f"Success. Transport fleet asset '{vehicle.transport_type}' permanently wiped from disk."}
