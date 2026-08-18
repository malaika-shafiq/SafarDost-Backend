from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from sqlalchemy.orm import Session
from database import get_db  # Optimized: Imported from core configuration layer
from models import Hotels
from schemas import hotel_schemas
from utils.auth_utils import get_current_admin

router = APIRouter(prefix="/hotels", tags=["Hotels Management"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_current_admin)]


@router.get("/", response_model=List[hotel_schemas.HotelResponse], status_code=status.HTTP_200_OK)
def get_all_hotels(db: db_dependency):
    """
    Fetches all registered hotels and accommodations across Pakistan for public browsing.
    """
    hotels = db.query(Hotels).all()
    return hotels


@router.get("/location/{location_name}", response_model=List[hotel_schemas.HotelResponse], status_code=status.HTTP_200_OK)
def get_hotels_by_location(location_name: str, db: db_dependency):
    """
    Filters hotels by location name using case-insensitive partial matching.
    """
    clean_location = location_name.strip()

    hotels = db.query(Hotels).filter(Hotels.location.ilike(f"%{clean_location}%")).all()

    if not hotels:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hotel accommodations registered under the location context: '{clean_location}'"
        )

    return hotels


@router.get("/{hotel_id}", response_model=hotel_schemas.HotelResponse, status_code=status.HTTP_200_OK)
def get_hotel_by_id(hotel_id: int, db: db_dependency):
    """
    Retrieves a single hotel's detailed record by its primary key ID.
    """
    hotel = db.query(Hotels).filter(Hotels.id == hotel_id).first()

    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel records not found for ID: {hotel_id}"
        )

    return hotel


@router.post("/", response_model=hotel_schemas.HotelResponse, status_code=status.HTTP_201_CREATED)
def create_hotel(hotel_request: hotel_schemas.HotelCreate, db: db_dependency, current_admin: admin_dependency):
    """
    Adds a brand-new hotel accommodation to the database. Strictly restricted to Admin users.
    """
    # ADD THIS EXPLICIT CHECK: Instantly blocks any regular user attempting to add data
    if current_admin.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to register new accommodations."
        )

    db_hotel = Hotels(**hotel_request.model_dump())
    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)
    return db_hotel

@router.put("/{hotel_id}", response_model=hotel_schemas.HotelResponse, status_code=status.HTTP_200_OK)
def update_hotel(hotel_id: int, hotel_request: hotel_schemas.HotelUpdate, db: db_dependency, current_admin: admin_dependency):
    """
    Modifies specific mutable fields of an existing hotel record dynamically. Strictly restricted to Admin users.
    """
    # ADD THIS EXPLICIT CHECK: Prevents regular users from modifying catalog prices
    if current_admin.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to modify accommodation metadata."
        )

    db_hotel = db.query(Hotels).filter(Hotels.id == hotel_id).first()
    if not db_hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel records not found for ID: {hotel_id}"
        )

    update_data = hotel_request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_hotel, key, value)

    db.commit()
    db.refresh(db_hotel)
    return db_hotel



@router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hotel(hotel_id: int, db: db_dependency, current_admin: admin_dependency):
    """
    Removes a hotel record permanently from the database. Strictly restricted to Admin users.
    """
    # ADD THIS EXPLICIT CHECK: Protects table row states from unauthorized removal requests
    if current_admin.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to purge accommodation data records."
        )

    db_hotel = db.query(Hotels).filter(Hotels.id == hotel_id).first()
    if not db_hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel records not found for ID: {hotel_id}"
        )

    db.delete(db_hotel)
    db.commit()
