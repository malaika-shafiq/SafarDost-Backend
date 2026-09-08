import math
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session, joinedload
from database import get_db

# Model and Schema Cross-Imports
from models.tour_package import TourPackages, PackageStatusEnum
from models.place import Places
from models.hotel import Hotels
from models.image import Images, ImageResourceTypeEnum
from schemas.tour_package_schemas import TourPackageCreate, TourPackageUpdate, TourPackageResponse
from utils.auth_utils import get_current_admin  # 🔒 Security Gate Dependency

router = APIRouter(prefix="/tour-packages", tags=["Predefined Tour Packages"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_current_admin)]


# ==========================================
# 1. READ ALL TOUR PACKAGES (Optimized Pagination, Search & Eager Loading)
# ==========================================
@router.get("", status_code=status.HTTP_200_OK)
def get_all_tour_packages_paginated(
        db: db_dependency,
        page: int = Query(1, ge=1, description="Page number starting from 1"),
        limit: int = Query(10, ge=1, le=50, description="Items per page"),
        search: Optional[str] = Query(None, description="Search across package name or details"),
        location_id: Optional[int] = Query(None, description="Filter packages by master location ID"),
        min_price: Optional[float] = Query(None, description="Minimum price filter metric"),
        max_price: Optional[float] = Query(None, description="Maximum price filter metric")
):
    """
    PUBLIC ACCESSIBLE: Browse and filter published tour packages [image_8Ld1yr].
    Eager-loads location profiles and uses batch mappings to completely stop inline query loops.
    """
    # 🏎️ ELIMINATES N+1 QUERY LOOP: Pre-fetches location nodes and checks active state records
    query = db.query(TourPackages).options(
        joinedload(TourPackages.location)
    ).filter(TourPackages.status == PackageStatusEnum.active)

    # 1. Apply Dynamic Text Search Bounds
    if search:
        query = query.filter(
            or_(
                TourPackages.name.ilike(f"%{search}%"),
                TourPackages.description.ilike(f"%{search}%"),
                TourPackages.activities.ilike(f"%{search}%")
            )
        )

    # 2. Apply Structural Filter Segments [image_8Ld1yr]
    if location_id:
        query = query.filter(TourPackages.location_id == location_id)
    if min_price is not None:
        query = query.filter(TourPackages.price >= min_price)
    if max_price is not None:
        query = query.filter(TourPackages.price <= max_price)

    # Order catalog results chronologically by latest publishing date
    query = query.order_by(desc(TourPackages.created_at))

    # 3. Extract Total Dataset Entry Counts Before Offsets
    total_items = query.count()

    # 4. Process DB Page Range Slices
    offset = (page - 1) * limit
    packages_list = query.offset(offset).limit(limit).all()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0

    # 5. Optimized Batch Image Processing to link photo strings in a single step
    package_ids = [p.id for p in packages_list]
    images_map = {}
    if package_ids:
        all_photos = db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.tour_package,
            Images.resource_id.in_(package_ids)
        ).all()
        for img in all_photos:
            if img.resource_id not in images_map:
                images_map[img.resource_id] = []
            images_map[img.resource_id].append(img.image_url)

    # 6. Map response payload array matching mobile UI expectation data models [image_8Ld1yr]
    items_response = []
    for package in packages_list:
        items_response.append({
            "id": package.id,
            "name": package.name,
            "description": package.description,
            "duration": package.duration,
            "price": package.price,
            "available_slots": package.available_slots,
            "start_date": package.start_date,
            "end_date": package.end_date,
            "activities": package.activities,
            "transportation_information": package.transportation_information,
            "included_services": package.included_services,
            "status": package.status,
            "location_id": package.location_id,
            "creator_id": package.creator_id,
            "updated_by": package.updated_by,
            "created_at": package.created_at,
            "updated_at": package.updated_at,
            # 🏛️ EXPLICIT RELATIONAL TEXT INCLUSIONS: Stops extra API calls from the client application
            "location_name": package.location.name if package.location else None,
            "images": images_map.get(package.id, []),
            # 🧠 AI-READY METRIC ARRAYS: Injects explicit included names arrays for client viewing tabs
            "included_places": [place.name for place in package.places],
            "included_hotels": [hotel.name for hotel in package.hotels]
        })

    return {
        "items": items_response,
        "total": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


# ==========================================
# 2. READ A SINGLE TOUR PACKAGE DETAIL PROFILE
# ==========================================
@router.get("/{package_id}", status_code=status.HTTP_200_OK)
def get_tour_package_by_id(package_id: int, db: db_dependency):
    """
    PUBLIC ACCESSIBLE: Fetch full itinerary information, list fields, and images for an item profile [image_8Ld1yr].
    """
    package = db.query(TourPackages).options(
        joinedload(TourPackages.location)
    ).filter(TourPackages.id == package_id).first()

    if not package:
        raise HTTPException(status_code=404, detail="Target tour package record not found.")

    photos = db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.tour_package,
        Images.resource_id == package_id
    ).all()

    return {
        "package": {
            "id": package.id,
            "name": package.name,
            "description": package.description,
            "duration": package.duration,
            "price": package.price,
            "available_slots": package.available_slots,
            "start_date": package.start_date,
            "end_date": package.end_date,
            "activities": package.activities,
            "transportation_information": package.transportation_information,
            "included_services": package.included_services,
            "status": package.status,
            "location_id": package.location_id,
            "creator_id": package.creator_id,
            "updated_by": package.updated_by,
            "created_at": package.created_at,
            "updated_at": package.updated_at,
            "location_name": package.location.name if package.location else None
        },
        "images": [img.image_url for img in photos],
        # 🏛️ DEEP NESTED OBJECT Blueprints: Pulls full entity details (IDs, coordinates, text attributes)
        "included_places": [{"id": p.id, "name": p.name, "latitude": p.latitude, "longitude": p.longitude} for p in
                            package.places],
        "included_hotels": [{"id": h.id, "name": h.name, "facilities": h.facilities} for h in package.hotels]
    }

# ==========================================
# 3. CREATE A TOUR PACKAGE (🔒 Admin Account Gate Only)
# ==========================================
@router.post("", status_code=status.HTTP_201_CREATED)
def create_new_tour_package(
        package_request: TourPackageCreate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Publishes a new structural tour package grid under strict audit log tracking [image_zFA75c].
    Automatically links multiple attraction spots and hotels into association tables at database level.
    """
    clean_name = package_request.name.strip()
    existing_package = db.query(TourPackages).filter(TourPackages.name.ilike(clean_name)).first()
    if existing_package:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A tour package bundle named '{clean_name}' already exists in your platform system directory."
        )

    # 1. Initialize main structural fields contract
    db_package = TourPackages(
        name=clean_name,
        description=package_request.description,
        duration=package_request.duration.strip(),
        price=package_request.price,
        available_slots=package_request.available_slots,
        start_date=package_request.start_date,
        end_date=package_request.end_date,
        activities=package_request.activities,
        transportation_information=package_request.transportation_information,
        included_services=package_request.included_services,
        location_id=package_request.location_id,
        creator_id=current_admin.get("id"), # 🏛️ Full administrative audit tracking signatures
        status=PackageStatusEnum.active
    )

    # 2. 🏛️ RESOLVE MANY-TO-MANY ATTRIBUTION BRIDGES: Fetch live records and bind collections
    if package_request.places_ids:
        verified_places = db.query(Places).filter(Places.id.in_(package_request.places_ids)).all()
        db_package.places = verified_places

    if package_request.hotels_ids:
        verified_hotels = db.query(Hotels).filter(Hotels.id.in_(package_request.hotels_ids)).all()
        db_package.hotels = verified_hotels

    db.add(db_package)
    db.commit()
    db.refresh(db_package)

    # 3. Automatically unroll incoming image pointer links into our unified polymorphic assets table
    for url in package_request.images:
        db_image = Images(
            image_url=url,
            resource_type=ImageResourceTypeEnum.tour_package,
            resource_id=db_package.id,
            creator_id=current_admin.get("id")
        )
        db.add(db_image)

    db.commit()
    return {"message": f"Tour package '{db_package.name}' launched successfully.", "package_id": db_package.id}


# ==========================================
# 4. UPDATE AN EXISTING TOUR PACKAGE (🔒 Admin Account Gate Only)
# ==========================================
@router.put("/{package_id}", status_code=status.HTTP_200_OK)
def update_tour_package(
        package_id: int,
        package_request: TourPackageUpdate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Modify tour package details, update slots, or re-assign included entities [image_Ay70D1].
    """
    package = db.query(TourPackages).filter(TourPackages.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Target tour package bundle record not found.")

    # 🏎️ PERFORMANCE REFACTOR: Uses partial dictionary un-setting mechanics safely
    update_data = package_request.model_dump(exclude_unset=True, exclude={"images", "places_ids", "hotels_ids"})
    for key, value in update_data.items():
        setattr(package, key, value)

    # 🏛️ AUDIT TRAIL ACCOUNTABILITY: Maps executing modifier admin context metrics securely
    package.updated_by = current_admin.get("id")

    # 🧠 RE-ALIGN LINK BRIDGE ID LISTS DYNAMICALLY IF SET IN REQUEST PAYLOADS
    if package_request.places_ids is not None:
        package.places = db.query(Places).filter(Places.id.in_(package_request.places_ids)).all()

    if package_request.hotels_ids is not None:
        package.hotels = db.query(Hotels).filter(Hotels.id.in_(package_request.hotels_ids)).all()

    # Process polymorphic photo updates if arrays are explicitly passed
    if package_request.images is not None:
        db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.tour_package,
            Images.resource_id == package_id
        ).delete()

        for url in package_request.images:
            db_image = Images(
                image_url=url,
                resource_type=ImageResourceTypeEnum.tour_package,
                resource_id=package_id,
                creator_id=current_admin.get("id")
            )
            db.add(db_image)

    db.commit()
    return {"message": f"Tour package '{package.name}' successfully modified and updated."}


# ==========================================
# 5. STAGE 1: SOFT-DELETE A TOUR PACKAGE (🔒 Admin Only Gate)
# ==========================================
@router.delete("/{package_id}", status_code=status.HTTP_200_OK)
def soft_delete_tour_package(
        package_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Stage-1 safe deactivation [image_Ay70D1]. Shifts status to 'inactive' to mask it from
    traveler search interfaces while preserving history and booking registries.
    """
    package = db.query(TourPackages).filter(TourPackages.id == package_id).first()
    if not package or package.status == PackageStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active tour package bundle profile not found or already deactivated."
        )

    # Trigger soft-delete status flags and record modification administrative ownership IDs
    package.status = PackageStatusEnum.inactive
    package.updated_by = current_admin.get("id")

    db.add(package)
    db.commit()
    return {"message": f"Tour package bundle '{package.name}' has been safely moved to inactive status."}


# ==========================================
# 6. STAGE 2: PERMANENT PURGE TOUR PACKAGE (🔒 Admin Only Gate)
# ==========================================
@router.delete("/{package_id}/purge", status_code=status.HTTP_200_OK)
def permanently_purge_tour_package(
        package_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Stage-2 hard delete sweep [image_Ay70D1]. Clears record row data lines from physical disk table storage
    and drops intermediate bridge links along with polymorphic photo url paths cleanly.
    """
    package = db.query(TourPackages).filter(TourPackages.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Target tour package record data not found.")

    # 🔒 TRASH BIN SAFETY GATE: Force them to soft-delete it first before executing a hard purge
    if package.status != PackageStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Lock: You must soft-delete this package profile before permanently purging it from memory."
        )

    # 🏛️ AUDIT LOGGING OVERRIDES: Actively uses the variable inputs context to prevent compile-time gray alerts!
    print(f"[SECURITY AUDIT LOG] Admin ID {current_admin.get('id')} is executing a permanent hard purge on tour package: {package.name}")

    # 1. Wipe nested polymorphic picture paths first to preserve database storage cleanliness
    db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.tour_package,
        Images.resource_id == package_id
    ).delete()

    # 2. Hard-delete the core catalog item from the primary database table disk (SQLAlchemy drops associations automatically)
    db.delete(package)
    db.commit()

    return {"message": f"Success. Tour package bundle '{package.name}' and all associated photo records permanently wiped from disk."}
