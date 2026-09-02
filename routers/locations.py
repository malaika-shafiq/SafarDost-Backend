from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.location import Locations, LocationStatusEnum
from schemas.location_schemas import LocationCreate, LocationResponse
from utils.auth_utils import get_current_admin

router = APIRouter(prefix="/locations", tags=["Locations Management"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_current_admin)]


# ==========================================
# 1. READ ALL LOCATIONS (Public / Traveler Mobile App Access)
# ==========================================
@router.get("", response_model=list[LocationResponse], status_code=status.HTTP_200_OK)
def get_all_locations(db: db_dependency):
    """
    PUBLIC ACCESSIBLE: Fetches all registered tourist regions (e.g., Hunza, Skardu)
    so travelers can browse options on their mobile device layouts.
    """
    return db.query(Locations).all()


# ==========================================
# 2. CREATE A LOCATION (🔒 Admin Account Gate Only)
# ==========================================
@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_new_location(
        location_request: LocationCreate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Inserts a new broad operational valley or city region into the system mapping.
    Prevents naming duplicates to ensure absolute data hygiene across Pakistan tracks.
    """
    clean_name = location_request.name.strip()
    # Performs a case-insensitive unique query check to prevent messy double inputs
    existing_location = db.query(Locations).filter(Locations.name.ilike(clean_name)).first()
    if existing_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A location profile for '{clean_name}' already exists in the system mapping."
        )

    db_location = Locations(
        name=clean_name,
        province_or_region=location_request.province_or_region.strip(),
        description=location_request.description,
        image_url=location_request.image_url,
        creator_id=current_admin.get("id")  # 🏛️ Full audit trails tracking captured here
    )

    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


# ==========================================
# 3. UPDATE A LOCATION (🔒 Admin Account Gate Only)
# ==========================================
@router.put("/{location_id}", response_model=LocationResponse, status_code=status.HTTP_200_OK)
def update_existing_location(
        location_id: int,
        location_request: LocationCreate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Modifies regional cover details, landscape paths, descriptions, or boundaries.
    """
    location = db.query(Locations).filter(Locations.id == location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target location profile does not exist inside our records."
        )

    # Re-verify unique naming constraint if the location name is altered
    clean_name = location_request.name.strip()
    if clean_name.lower() != location.name.lower():
        name_check = db.query(Locations).filter(Locations.name.ilike(clean_name)).first()
        if name_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot rename location; a region named '{clean_name}' already exists."
            )

    location.name = clean_name
    location.province_or_region = location_request.province_or_region.strip()
    location.description = location_request.description
    location.image_url = location_request.image_url
    location.updated_by = current_admin.get("id")

    db.add(location)
    db.commit()
    db.refresh(location)  # 👈 FIXED: Syncs memory variables before serialization
    return location


# ==========================================
# 4. DELETE A LOCATION (🔒 Admin Account Gate Only)
# ==========================================
@router.delete("/{location_id}", status_code=status.HTTP_200_OK)
def soft_delete_location(
        location_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Deactivates a location profile safely by changing status to 'inactive'.
    Prevents database cascades from breaking connected attractions or hotels.
    """
    location = db.query(Locations).filter(Locations.id == location_id).first()

    if not location or location.status == LocationStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location record not found or already deactivated."
        )

    # 🏛️ Apply the soft-delete enum state and track who did it
    location.status = LocationStatusEnum.inactive
    location.updated_by = current_admin.get("id")  # Uses the variable to clear PyCharm's warning!

    db.add(location)
    db.commit()
    return {"message": f"Regional profile '{location.name}' has been safely deactivated and soft-deleted."}

