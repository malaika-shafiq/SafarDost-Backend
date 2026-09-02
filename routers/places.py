import math
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session, joinedload
from database import get_db

# Model and Schema Cross-Imports
from models.place import Places, PlaceStatusEnum  # 👈 IMPORTED ENUM HERE
from models.image import Images, ImageResourceTypeEnum
from schemas.place_schemas import PlaceCreate, PlaceUpdate, PlaceResponse, PlaceDetailResponse
from utils.auth_utils import get_current_admin  # 🔒 Security Gate Dependency

router = APIRouter(prefix="/places", tags=["Tourist Places Module"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_current_admin)]


# ==========================================
# 1. READ ALL PLACES (With Pagination, Search, Filtering & Sorting)
# ==========================================
@router.get("", status_code=status.HTTP_200_OK)
def get_all_places_paginated(
        db: db_dependency,
        page: int = Query(1, ge=1, description="Page number starting from 1"),
        limit: int = Query(10, ge=1, le=50, description="Items per page"),
        search: Optional[str] = Query(None, description="Search across place name or physical address landmarks"),
        location_id: Optional[int] = Query(None, description="Filter attractions by master location ID"),
        category_id: Optional[int] = Query(None, description="Filter attractions by master category ID"),
        sort_by: str = Query("id", description="Field to sort by (id, name, created_at)"),
        order: str = Query("desc", description="Sort execution order (asc or desc)")
):
    """
    PUBLIC ACCESSIBLE: Advanced discovery endpoint for mobile travelers.
    Optimized with eager loading to eliminate database N+1 bottleneck queries.
    """
    # 🏎️ FIXED N+1 PROBLEM: Pre-fetch full object relationships using joinedload
    # 🏎️ ENUM ALIGNMENT: Filters exclusively for active database states
    query = db.query(Places).options(
        joinedload(Places.category),
        joinedload(Places.location)
    ).filter(Places.status == PlaceStatusEnum.active)

    # 1. Apply Search Filter Bounds
    if search:
        query = query.filter(
            or_(
                Places.name.ilike(f"%{search}%"),
                Places.physical_address.ilike(f"%{search}%")
            )
        )

    # 2. Apply Foreign Key Lookups
    if location_id:
        query = query.filter(Places.location_id == location_id)
    if category_id:
        query = query.filter(Places.category_id == category_id)

    # 3. Handle Dynamic Sorting Logic
    sort_column = getattr(Places, sort_by, Places.id)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # 4. Extract Total Counts Before Offsets
    total_items = query.count()

    # 5. Process DB Page Range Slices
    offset = (page - 1) * limit
    places_list = query.offset(offset).limit(limit).all()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0

    # 6. Optimized Batch Image Loading mapping loop to completely stop separate inline hits
    place_ids = [p.id for p in places_list]
    images_map = {}
    if place_ids:
        all_photos = db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.place,
            Images.resource_id.in_(place_ids)
        ).all()
        for img in all_photos:
            if img.resource_id not in images_map:
                images_map[img.resource_id] = []
            images_map[img.resource_id].append(img.image_url)

    # 7. Package structured response array matching mobile screen expectations
    items_response = []
    for place in places_list:
        items_response.append({
            "id": place.id,
            "name": place.name,
            "description": place.description,
            "latitude": place.latitude,
            "longitude": place.longitude,
            "physical_address": place.physical_address,
            "entry_information": place.entry_information,
            "recommended_visiting_information": place.recommended_visiting_information,
            "travel_tips": place.travel_tips,
            "status": place.status,
            "location_id": place.location_id,
            "category_id": place.category_id,
            "creator_id": place.creator_id,
            "updated_by": place.updated_by,
            "created_at": place.created_at,
            "updated_at": place.updated_at,
            # 🏛️ RELATIONAL OBJ EMBEDDING: Passes direct text values straight to client UI layouts
            "location_name": place.location.name if place.location else None,
            "category_name": place.category.name if place.category else None,
            "images": images_map.get(place.id, [])
        })

    return {
        "items": items_response,
        "total": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


# ==========================================
# 2. READ A SINGLE PLACE PROFILE DETAILS
# ==========================================
@router.get("/{place_id}", response_model=PlaceDetailResponse, status_code=status.HTTP_200_OK)
def get_place_by_id(place_id: int, db: db_dependency):
    """
    PUBLIC ACCESSIBLE: Fetch deep metadata details and full photo asset arrays for a single attraction target.
    """
    place = db.query(Places).options(
        joinedload(Places.category),
        joinedload(Places.location)
    ).filter(Places.id == place_id).first()

    if not place:
        raise HTTPException(status_code=404, detail="Target tourist attraction spot not found.")

    photos = db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.place,
        Images.resource_id == place_id
    ).all()

    # 🏛️ FIXED PAYLOAD: Packages fields safely inside 'place' to match your validation schema model
    return {
        "place": {
            "id": place.id,
            "name": place.name,
            "description": place.description,
            "latitude": place.latitude,
            "longitude": place.longitude,
            "physical_address": place.physical_address,
            "entry_information": place.entry_information,
            "recommended_visiting_information": place.recommended_visiting_information,
            "travel_tips": place.travel_tips,
            "status": place.status,
            "location_id": place.location_id,
            "category_id": place.category_id,
            "creator_id": place.creator_id,
            "updated_by": place.updated_by,
            "created_at": place.created_at,
            "updated_at": place.updated_at
        },
        "images": [img.image_url for img in photos]
    }



# ==========================================
# 3. CREATE A TOURIST PLACE (🔒 Admin Account Gate Only)
# ==========================================
@router.post("", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
def create_tourist_place(
        place_request: PlaceCreate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Inserts a new northern region destination point and maps image arrays polymorphically.
    """
    clean_name = place_request.name.strip()
    existing_spot = db.query(Places).filter(
        Places.name.ilike(clean_name),
        Places.location_id == place_request.location_id
    ).first()

    if existing_spot:
        raise HTTPException(
            status_code=400,
            detail=f"An attraction spot profile named '{clean_name}' already exists for this regional location node."
        )

    db_place = Places(
        name=clean_name,
        description=place_request.description,
        latitude=place_request.latitude,
        longitude=place_request.longitude,
        physical_address=place_request.physical_address,
        entry_information=place_request.entry_information,
        recommended_visiting_information=place_request.recommended_visiting_information,
        travel_tips=place_request.travel_tips,
        location_id=place_request.location_id,
        category_id=place_request.category_id,
        creator_id=current_admin.get("id")
    )

    db.add(db_place)
    db.commit()
    db.refresh(db_place)

    for url in place_request.images:
        db_image = Images(
            image_url=url,
            resource_type=ImageResourceTypeEnum.place,
            resource_id=db_place.id,
            creator_id=current_admin.get("id")
        )
        db.add(db_image)

    db.commit()
    return db_place


# ==========================================
# 4. UPDATE AN EXISTING TOURIST PLACE (🔒 Admin Account Gate Only)
# ==========================================
@router.put("/{place_id}", response_model=PlaceResponse, status_code=status.HTTP_200_OK)
def update_tourist_place(
        place_id: int,
        place_request: PlaceUpdate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Update attraction information parameters and trace changes dynamically.
    Safely ignores unset fields to prevent accidental payload overrides.
    """
    place = db.query(Places).filter(Places.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Tourist attraction profile not found.")

    # 🏎️ PERFORMANCE REFACTOR: Uses partial dictionary un-setting mechanics safely
    update_data = place_request.model_dump(exclude_unset=True, exclude={"images"})
    for key, value in update_data.items():
        setattr(place, key, value)

    # 🏛️ AUDIT TRAIL LOGGING: Actively maps executing admin ID context variables
    place.updated_by = current_admin.get("id")

    # Handle structural photo replacements if image arrays are explicitly passed
    if place_request.images is not None:
        # First wipe previous image maps to prevent leftover file orphans
        db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.place,
            Images.resource_id == place_id
        ).delete()

        # Insert fresh image mapping list collections
        for url in place_request.images:
            db_image = Images(
                image_url=url,
                resource_type=ImageResourceTypeEnum.place,
                resource_id=place_id,
                creator_id=current_admin.get("id")
            )
            db.add(db_image)

    db.commit()
    db.refresh(place)
    return place


# ==========================================
# 5. STAGE 1: SOFT-DELETE AN ATTRACTION (🔒 Admin Only)
# ==========================================
@router.delete("/{place_id}", status_code=status.HTTP_200_OK)
def soft_delete_tourist_place(
        place_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Safe stage-1 deletion. Shifts status to 'inactive' to hide the spot
    from mobile traveler search feeds while preserving historic review logs.
    """
    place = db.query(Places).filter(Places.id == place_id).first()

    # 🏎️ ENUM LOCKDOWN: Performs safe string comparisons against modern system standards
    if not place or place.status == PlaceStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active tourist attraction spot not found or already deactivated."
        )

    # Apply soft-delete switches and record accountability audit trails
    place.status = PlaceStatusEnum.inactive
    place.updated_by = current_admin.get("id")

    db.add(place)
    db.commit()
    return {"message": f"Attraction '{place.name}' has been safely moved to inactive status."}


# ==========================================
# 6. STAGE 2: PERMANENT PURGE ATTRACTION (🔒 Admin Only)
# ==========================================
@router.delete("/{place_id}/purge", status_code=status.HTTP_200_OK)
def permanently_purge_tourist_place(
        place_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Stage-2 absolute deletion. Permanently wipes the row from disk
    storage and strips out related polymorphic image URLs cleanly.
    """
    place = db.query(Places).filter(Places.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Target attraction record not found.")

    # TRASH BIN SAFETY GATE: Force them to soft-delete it first before executing a hard purge
    if place.status != PlaceStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Lock: You must soft-delete this place before permanently purging it from storage."
        )

    # 🏛️ AUDIT TRAIL LOGGING: Actively uses the variable payload to clear the PyCharm alert warning!
    print(f"[SECURITY AUDIT] Admin ID {current_admin.get('id')} is executing a permanent hard purge on attraction: {place.name}")

    # 1. Clean out nested polymorphic picture rows first to prevent table clutter
    db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.place,
        Images.resource_id == place_id
    ).delete()

    # 2. Hard-delete the core record item from the physical database table disk
    db.delete(place)
    db.commit()

    return {"message": f"Success. Attraction record '{place.name}' and all connected photo assets permanently purged."}
