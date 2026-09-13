from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from typing import List

from models.user_trip import UserTrips, TripScopeEnum
from schemas.user_trip_schemas import UserTripCreate, UserTripUpdate, UserTripResponse
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/trips", tags=["User Trips History & Planning Ledger"])


# ==========================================
# 1. READ ALL TRIPS (Traveler Timeline View)
# ==========================================
@router.get("", response_model=List[UserTripResponse], status_code=status.HTTP_200_OK)
def get_user_trip_ledger(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """ Returns the authenticated traveler's entire current and past trip histories chronologically. """
    return db.query(UserTrips).filter(
        UserTrips.user_id == current_user.get("id")
    ).order_by(UserTrips.start_date.desc()).all()


# ==========================================
# 2. CREATE A NEW TRIP RECORD (Manual or via AI)
# ==========================================
@router.post("", response_model=UserTripResponse, status_code=status.HTTP_201_CREATED)
def create_new_trip_record(
        trip_data: UserTripCreate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Allows a traveler to manually log an itinerary or commit an AI-generated plan directly onto their dashboard.
    Automatically archives older trips if the new one is set to 'current'.
    """
    # 🛑 AUTOMATED STATE ARCHIVER: If marking this new trip as 'current',
    # flip all existing active trips to 'history' so the user has exactly one active journey.
    if trip_data.scope == TripScopeEnum.current:
        db.query(UserTrips).filter(
            UserTrips.user_id == current_user.get("id"),
            UserTrips.scope == TripScopeEnum.current
        ).update({"scope": TripScopeEnum.history.value})

    db_trip = UserTrips(
        user_id=current_user.get("id"),
        trip_title=trip_data.trip_title.strip(),
        destination=trip_data.destination.strip(),
        start_date=trip_data.start_date,
        end_date=trip_data.end_date,
        itinerary_details=trip_data.itinerary_details.strip(),
        scope=trip_data.scope
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip


# ==========================================
# 3. UPDATE AN EXISTING TRIP (Manual Modifications)
# ==========================================
@router.put("/{trip_id}", response_model=UserTripResponse, status_code=status.HTTP_200_OK)
def update_existing_trip_record(
        trip_id: int,
        trip_request: UserTripUpdate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """ Modifies custom travel notes, dates, or moves an active trip to history. Protects account boundaries. """
    # 🔒 Ownership Boundary Guardrail: Ensure users can only edit their own trips
    db_trip = db.query(UserTrips).filter(
        UserTrips.id == trip_id,
        UserTrips.user_id == current_user.get("id")
    ).first()

    if not db_trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target travel itinerary record not found or unauthorized access."
        )

    # 🛑 AUTOMATED STATE ARCHIVER: If shifting this trip's scope to 'current', demote all others to 'history'
    if trip_request.scope == TripScopeEnum.current and db_trip.scope != TripScopeEnum.current:
        db.query(UserTrips).filter(
            UserTrips.user_id == current_user.get("id"),
            UserTrips.scope == TripScopeEnum.current
        ).update({"scope": TripScopeEnum.history.value})

    # Unroll incoming payload dynamically using Pydantic parameters
    update_data = trip_request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_trip, key, value)

    db.commit()
    db.refresh(db_trip)
    return db_trip


# ==========================================
# 4. HARD DELETE A TRIP RECORD (Wipe from Disk)
# ==========================================
@router.delete("/{trip_id}", status_code=status.HTTP_200_OK)
def delete_historical_trip_record(
        trip_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """ Permanently removes a specific trip itinerary from the database disk layout safely. """
    # 🔒 Ownership Boundary Guardrail: Locate the trip only if it belongs to the logged-in traveler
    db_trip = db.query(UserTrips).filter(
        UserTrips.id == trip_id,
        UserTrips.user_id == current_user.get("id")
    ).first()

    if not db_trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target travel itinerary record not found or unauthorized access."
        )

    print(f"[TRIP PURGE AUDIT] User ID {current_user.get('id')} deleted Trip ID: {db_trip.id}")

    db.delete(db_trip)
    db.commit()
    return {"message": f"Success. Trip itinerary '{db_trip.trip_title}' has been permanently wiped from your history."}
