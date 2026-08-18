from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from sqlalchemy.orm import Session
from database import get_db
from models.restaurant import Restaurants
from schemas import restaurant_schemas
from utils.auth_utils import get_current_admin

router = APIRouter(prefix="/restaurants", tags=["Restaurants Management"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_current_admin)]


@router.get("/", response_model=List[restaurant_schemas.RestaurantResponse], status_code=status.HTTP_200_OK)
def get_all_restaurants(db: db_dependency, price_range: str = None):
    """
    Fetches all registered restaurants across Pakistan for public browsing.
    Optional query parameter:
    - price_range: Filters restaurants by tier using partial pattern matching (e.g., Budget, Luxury).
    """
    query = db.query(Restaurants)

    if price_range:
        clean_price = price_range.strip()
        # Optimized to use partial wildcard matching for smooth mobile user searches
        query = query.filter(Restaurants.price_range.ilike(f"%{clean_price}%"))

    return query.all()


@router.get("/location/{location_name}", response_model=List[restaurant_schemas.RestaurantResponse],
            status_code=status.HTTP_200_OK)
def get_restaurants_by_location(location_name: str, db: db_dependency):
    """
    Filters restaurants by location name using case-insensitive partial matching.
    """
    clean_location = location_name.strip()

    restaurants = db.query(Restaurants).filter(Restaurants.location.ilike(f"%{clean_location}%")).all()

    if not restaurants:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No restaurants registered under the location context: '{clean_location}'"
        )

    return restaurants


@router.get("/{restaurant_id}", response_model=restaurant_schemas.RestaurantResponse, status_code=status.HTTP_200_OK)
def get_restaurant_by_id(restaurant_id: int, db: db_dependency):
    """
    Retrieves a single restaurant's detailed record by its primary key ID.
    """
    restaurant = db.query(Restaurants).filter(Restaurants.id == restaurant_id).first()

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant records not found for ID: {restaurant_id}"
        )

    return restaurant


@router.post("/", response_model=restaurant_schemas.RestaurantResponse, status_code=status.HTTP_201_CREATED)
def create_restaurant(restaurant_request: restaurant_schemas.RestaurantCreate, db: db_dependency,
                      current_admin: admin_dependency):
    """
    Adds a brand-new restaurant to the database. Strictly restricted to Admin users.
    """
    # 🔒 SECURE CHECK: Stop regular users from adding new restaurants to the directory
    if current_admin.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to register new restaurants."
        )

    # Map incoming JSON fields directly to your SQLAlchemy table columns via unpacking mapping
    db_restaurant = Restaurants(**restaurant_request.model_dump())

    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)

    return db_restaurant

@router.put("/{restaurant_id}", response_model=restaurant_schemas.RestaurantResponse, status_code=status.HTTP_200_OK)
def update_restaurant(restaurant_id: int, restaurant_request: restaurant_schemas.RestaurantUpdate, db: db_dependency,
                      current_admin: admin_dependency):
    """
    Modifies specific mutable fields of an existing restaurant record dynamically. Strictly restricted to Admin users.
    """
    # 🔒 SECURE CHECK: Prevent non-admin users from updating menus, tiers, or details
    if current_admin.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to modify restaurant metadata."
        )

    db_restaurant = db.query(Restaurants).filter(Restaurants.id == restaurant_id).first()

    if not db_restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant records not found for ID: {restaurant_id}"
        )

    update_data = restaurant_request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_restaurant, key, value)

    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_restaurant(restaurant_id: int, db: db_dependency, current_admin: admin_dependency):
    """
    Removes a restaurant record permanently from the database. Strictly restricted to Admin users.
    """
    # 🔒 SECURE CHECK: Protect dinner listings from unauthorized deletion requests
    if current_admin.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to purge restaurant records."
        )

    db_restaurant = db.query(Restaurants).filter(Restaurants.id == restaurant_id).first()

    if not db_restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant records not found for ID: {restaurant_id}"
        )

    db.delete(db_restaurant)
    db.commit()