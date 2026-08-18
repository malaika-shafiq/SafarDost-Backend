from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from sqlalchemy.orm import Session
from database import get_db  # Optimized: Imported from core configuration layer
from models.place import Places
from schemas import place_schemas
from utils.auth_utils import get_current_admin

router = APIRouter(prefix="/places", tags=["Tourist Places"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_current_admin)]


@router.get("/", response_model=List[place_schemas.PlaceResponse], status_code=status.HTTP_200_OK)
def get_all_places(db: db_dependency):
    """
    Fetches all registered iconic tourist locations across Pakistan for public browsing.
    """
    places = db.query(Places).all()
    return places


@router.get("/location/{location_name}", response_model=List[place_schemas.PlaceResponse], status_code=status.HTTP_200_OK)
def get_places_by_location(location_name: str, db: db_dependency):
    """
    Filters tourist spots by location name using case-insensitive partial matching.
    Aligned to match the robust hotel module filtering blueprint.
    """
    clean_location = location_name.strip()

    # Optimized to use partial wildcard matching for an improved mobile user experience
    places = db.query(Places).filter(Places.location.ilike(f"%{clean_location}%")).all()

    if not places:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No tourist spots registered under the location context: '{clean_location}'"
        )

    return places


@router.get("/category/{category_name}", response_model=List[place_schemas.PlaceResponse], status_code=status.HTTP_200_OK)
def get_places_by_category(category_name: str, db: db_dependency):
    """
    Filters tourist destinations by categorical type (e.g., Lake, Valley, Fort).
    """
    clean_category = category_name.strip()

    places = db.query(Places).filter(Places.category.ilike(clean_category)).all()

    if not places:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No tourist spots discovered under category: '{clean_category}'"
        )

    return places


@router.get("/{place_id}", response_model=place_schemas.PlaceResponse, status_code=status.HTTP_200_OK)
def get_place_by_id(place_id: int, db: db_dependency):
    """
    Retrieves a single tourist destination's details by its primary key ID.
    """
    place = db.query(Places).filter(Places.id == place_id).first()

    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tourist place records not found for ID: {place_id}"
        )

    return place


@router.post("/", response_model=place_schemas.PlaceResponse, status_code=status.HTTP_201_CREATED)
def create_tourist_place(place_request: place_schemas.PlaceCreate, db: db_dependency, current_admin: admin_dependency):
    """
    Adds a brand new iconic Pakistani tourist destination to the database. Strictly restricted to Admin users.
    """
    # 🔒 SECURE CHECK: Block regular users from publishing new tourist spots
    if current_admin.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to register new tourist destinations."
        )

    db_place = Places(**place_request.model_dump())

    db.add(db_place)
    db.commit()
    db.refresh(db_place)

    return db_place


@router.put("/{place_id}", response_model=place_schemas.PlaceResponse, status_code=status.HTTP_200_OK)
def update_tourist_place(place_id: int, place_request: place_schemas.PlaceUpdate, db: db_dependency, current_admin: admin_dependency):
    """
    Modifies an existing tourist place's attributes dynamically. Strictly restricted to Admin users.
    """
    # 🔒 SECURE CHECK: Stop unauthorized accounts from altering landmark details
    if current_admin.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to modify destination information."
        )

    db_place = db.query(Places).filter(Places.id == place_id).first()

    if not db_place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tourist place records not found for ID: {place_id}"
        )

    update_data = place_request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_place, key, value)

    db.commit()
    db.refresh(db_place)
    return db_place



@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tourist_place(place_id: int, db: db_dependency, current_admin: admin_dependency):
    """
    Permanently deletes a tourist destination from the database. Strictly restricted to Admin users.
    """
    # 🔒 SECURE CHECK: Prevent normal users from wiping out locations from SQLite
    if current_admin.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to remove destinations from the platform."
        )

    db_place = db.query(Places).filter(Places.id == place_id).first()

    if not db_place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tourist place records not found for ID: {place_id}"
        )

    db.delete(db_place)
    db.commit()