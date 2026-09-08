import math
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session, joinedload
from database import get_db

# Model and Schema Cross-Imports
from models.restaurant import Restaurants, RestaurantStatusEnum
from models.image import Images, ImageResourceTypeEnum
from schemas.restaurant_schemas import RestaurantCreate, RestaurantUpdate, RestaurantResponse, RestaurantDetailResponse
from utils.auth_utils import get_current_admin  # 🔒 Security Gate Dependency

router = APIRouter(prefix="/restaurants", tags=["Restaurants Management Module"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_current_admin)]


# ==========================================
# 1. READ ALL RESTAURANTS (Optimized Pagination, Search & Eager Loading)
# ==========================================
@router.get("", status_code=status.HTTP_200_OK)
def get_all_restaurants_paginated(
        db: db_dependency,
        page: int = Query(1, ge=1, description="Page number starting from 1"),
        limit: int = Query(10, ge=1, le=50, description="Items per page"),
        search: Optional[str] = Query(None, description="Search across restaurant name, cuisine or details"),
        location_id: Optional[int] = Query(None, description="Filter restaurants by master location ID"),
        category_id: Optional[int] = Query(None, description="Filter restaurants by master category ID"),
        sort_by: str = Query("id", description="Field to sort by (id, name, created_at)"),
        order: str = Query("desc", description="Sort execution order (asc or desc)")
):
    """
    PUBLIC ACCESSIBLE: Advanced discovery endpoint for mobile travelers.
    Employs 'joinedload' to pre-fetch taxonomy details and filter active items seamlessly.
    """
    # 🏎️ FIXED N+1 QUERY BOTTLENECK: Eager-load relationships and filter for active records
    query = db.query(Restaurants).options(
        joinedload(Restaurants.category),
        joinedload(Restaurants.location)
    ).filter(Restaurants.status == RestaurantStatusEnum.active)

    # 1. Apply Dynamic Search Text Bounds
    if search:
        query = query.filter(
            or_(
                Restaurants.name.ilike(f"%{search}%"),
                Restaurants.cuisine.ilike(f"%{search}%"),
                Restaurants.description.ilike(f"%{search}%")
            )
        )

    # 2. Apply Optional Foreign Key Segment Filters
    if location_id:
        query = query.filter(Restaurants.location_id == location_id)
    if category_id:
        query = query.filter(Restaurants.category_id == category_id)

    # 3. Process Dynamic Sorting Constraints
    sort_column = getattr(Restaurants, sort_by, Restaurants.id)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # 4. Extract Total Dataset Entry Counts Before Offsets
    total_items = query.count()

    # 5. Process DB Page Range Slices
    offset = (page - 1) * limit
    restaurants_list = query.offset(offset).limit(limit).all()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0

    # 6. Optimized Batch Image Processing to completely stop separate inline loops
    restaurant_ids = [r.id for r in restaurants_list]
    images_map = {}
    if restaurant_ids:
        all_photos = db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.restaurant,
            Images.resource_id.in_(restaurant_ids)
        ).all()
        for img in all_photos:
            if img.resource_id not in images_map:
                images_map[img.resource_id] = []
            images_map[img.resource_id].append(img.image_url)

    # 7. Map payload response safely including relational database text strings
    items_response = []
    for restaurant in restaurants_list:
        items_response.append({
            "id": restaurant.id,
            "name": restaurant.name,
            "description": restaurant.description,
            "cuisine": restaurant.cuisine,
            "menu_details": restaurant.menu_details,
            "price_range": restaurant.price_range,
            "contact": restaurant.contact,
            "opening_information": restaurant.opening_information,
            "table_capacity": restaurant.table_capacity,
            "status": restaurant.status,
            "location_id": restaurant.location_id,
            "category_id": restaurant.category_id,
            "creator_id": restaurant.creator_id,
            "updated_by": restaurant.updated_by,
            "created_at": restaurant.created_at,
            "updated_at": restaurant.updated_at,
            # 🏛️ RELATIONAL INCLUSIONS: Allows the app to render titles natively without extra lookups
            "location_name": restaurant.location.name if restaurant.location else None,
            "category_name": restaurant.category.name if restaurant.category else None,
            "images": images_map.get(restaurant.id, [])
        })

    return {
        "items": items_response,
        "total": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


# ==========================================
# 2. READ A SINGLE RESTAURANT PROFILE DETAILS
# ==========================================
@router.get("/{restaurant_id}", response_model=RestaurantDetailResponse, status_code=status.HTTP_200_OK)
def get_restaurant_by_id(restaurant_id: int, db: db_dependency):
    """
    PUBLIC ACCESSIBLE: Fetch deep profile parameters and photo strings array list for a target establishment.
    """
    restaurant = db.query(Restaurants).options(
        joinedload(Restaurants.category),
        joinedload(Restaurants.location)
    ).filter(Restaurants.id == restaurant_id).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Target restaurant profile record not found.")

    photos = db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.restaurant,
        Images.resource_id == restaurant_id
    ).all()

    return {
        "restaurant": {
            "id": restaurant.id,
            "name": restaurant.name,
            "description": restaurant.description,
            "cuisine": restaurant.cuisine,
            "menu_details": restaurant.menu_details,
            "price_range": restaurant.price_range,
            "contact": restaurant.contact,
            "opening_information": restaurant.opening_information,
            "table_capacity": restaurant.table_capacity,
            "status": restaurant.status,
            "location_id": restaurant.location_id,
            "category_id": restaurant.category_id,
            "creator_id": restaurant.creator_id,
            "updated_by": restaurant.updated_by,
            "created_at": restaurant.created_at,
            "updated_at": restaurant.updated_at
        },
        "images": [img.image_url for img in photos]
    }


# ==========================================
# 3. CREATE A RESTAURANT (🔒 Admin Account Gate Only)
# ==========================================
@router.post("", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
def create_new_restaurant(
        restaurant_request: RestaurantCreate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Inserts a new hospitality dining spot under direct accountability tracking records.
    Unfolds request image array pointers smoothly into the central polymorphic engine.
    """
    clean_name = restaurant_request.name.strip()
    existing_spot = db.query(Restaurants).filter(
        Restaurants.name.ilike(clean_name),
        Restaurants.location_id == restaurant_request.location_id
    ).first()

    if existing_spot:
        raise HTTPException(
            status_code=400,
            detail=f"A dining spot profile named '{clean_name}' already exists inside this regional destination node."
        )

    db_restaurant = Restaurants(
        name=clean_name,
        description=restaurant_request.description,
        cuisine=restaurant_request.cuisine.strip(),
        menu_details=restaurant_request.menu_details,
        price_range=restaurant_request.price_range,
        contact=restaurant_request.contact.strip(),
        opening_information=restaurant_request.opening_information.strip(),
        table_capacity=restaurant_request.table_capacity,
        location_id=restaurant_request.location_id,
        category_id=restaurant_request.category_id,
        creator_id=current_admin.get("id")  # 🏛️ Full audit signature mapping
    )

    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)

    # Automatically unrolls incoming string urls directly into our central media repository table
    for url in restaurant_request.images:
        db_image = Images(
            image_url=url,
            resource_type=ImageResourceTypeEnum.restaurant,
            resource_id=db_restaurant.id,
            creator_id=current_admin.get("id")
        )
        db.add(db_image)

    db.commit()
    return db_restaurant

# ==========================================
# 4. UPDATE AN EXISTING RESTAURANT (🔒 Admin Account Gate Only)
# ==========================================
@router.put("/{restaurant_id}", response_model=RestaurantResponse, status_code=status.HTTP_200_OK)
def update_restaurant(
        restaurant_id: int,
        restaurant_request: RestaurantUpdate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Modify existing dining spot attributes and trace structural changes.
    Safely ignores unset fields to prevent accidental payload overrides.
    """
    restaurant = db.query(Restaurants).filter(Restaurants.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Target restaurant profile record not found.")

    # 🏎️ PERFORMANCE REFACTOR: Uses partial dictionary un-setting mechanics safely
    update_data = restaurant_request.model_dump(exclude_unset=True, exclude={"images"})
    for key, value in update_data.items():
        setattr(restaurant, key, value)

    # 🏛️ AUDIT TRAIL LOGGING: Actively maps executing admin ID context variables to clear warnings
    restaurant.updated_by = current_admin.get("id")

    # Handle structural photo replacements if image arrays are explicitly passed
    if restaurant_request.images is not None:
        # First wipe previous image maps to prevent leftover file orphans
        db.query(Images).filter(
            Images.resource_type == ImageResourceTypeEnum.restaurant,
            Images.resource_id == restaurant_id
        ).delete()

        # Insert fresh image mapping list collections
        for url in restaurant_request.images:
            db_image = Images(
                image_url=url,
                resource_type=ImageResourceTypeEnum.restaurant,
                resource_id=restaurant_id,
                creator_id=current_admin.get("id")
            )
            db.add(db_image)

    db.commit()
    db.refresh(restaurant)
    return restaurant


# ==========================================
# 5. STAGE 1: SOFT-DELETE A RESTAURANT (🔒 Admin Only)
# ==========================================
@router.delete("/{restaurant_id}", status_code=status.HTTP_200_OK)
def soft_delete_restaurant(
        restaurant_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Safe stage-1 deletion. Shifts status to 'inactive' to hide the eatery
    from mobile traveler feeds while preserving historic transaction logs and reviews.
    """
    restaurant = db.query(Restaurants).filter(Restaurants.id == restaurant_id).first()

    # 🏎️ ENUM LOCKDOWN: Performs safe comparisons against modern system standards
    if not restaurant or restaurant.status == RestaurantStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active restaurant profile not found or already deactivated."
        )

    # Apply soft-delete switches and record accountability audit trails
    restaurant.status = RestaurantStatusEnum.inactive
    restaurant.updated_by = current_admin.get("id")

    db.add(restaurant)
    db.commit()
    return {"message": f"Restaurant '{restaurant.name}' has been safely moved to inactive status."}


# ==========================================
# 6. STAGE 2: PERMANENT PURGE RESTAURANT (🔒 Admin Only)
# ==========================================
@router.delete("/{restaurant_id}/purge", status_code=status.HTTP_200_OK)
def permanently_purge_restaurant(
        restaurant_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Stage-2 absolute deletion. Permanently wipes the row from disk
    storage and strips out related polymorphic image URLs cleanly.
    """
    restaurant = db.query(Restaurants).filter(Restaurants.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Target restaurant record not found.")

    # 🔒 TRASH BIN SAFETY GATE: Force them to soft-delete it first before executing a hard purge
    if restaurant.status != RestaurantStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Lock: You must soft-delete this restaurant before permanently purging it from storage."
        )

    # 🏛️ AUDIT TRAIL LOGGING: Actively uses the variable payload to clear the PyCharm alert warning!
    print(f"[SECURITY AUDIT] Admin ID {current_admin.get('id')} is executing a permanent hard purge on restaurant: {restaurant.name}")

    # 1. Clean out nested polymorphic picture rows first to prevent table clutter
    db.query(Images).filter(
        Images.resource_type == ImageResourceTypeEnum.restaurant,
        Images.resource_id == restaurant_id
    ).delete()

    # 2. Hard-delete the core record item from the physical database table disk
    db.delete(restaurant)
    db.commit()

    return {"message": f"Success. Restaurant record '{restaurant.name}' and all connected photo assets permanently purged."}
