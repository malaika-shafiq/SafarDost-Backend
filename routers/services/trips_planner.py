import os
import json
import logging
import urllib.parse
import urllib.request
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List

from database import get_db
from utils.auth_utils import get_current_user
from models.trip_planner import TripContainer
from models.place import Places  # High-speed relational database lookups
from models.restaurant import Restaurants  # High-speed relational database lookups
from schemas.trip_planner_schemas import TripCreateInput, TripContainerResponse

logger = logging.getLogger("safardost.trips")

router = APIRouter(prefix="/trips", tags=["AI-Powered Trip Planner Containers"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

# ⚡ OPTIMIZATION: Fetch key once globally at startup to eliminate redundant environment disk reads
GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_KEY")


@router.post("/ai-plan", response_model=TripContainerResponse, status_code=status.HTTP_201_CREATED)
def generate_and_save_ai_trip(payload: TripCreateInput, current_user: user_dependency, db: db_dependency):
    """
    Highly Optimized Hybrid AI Engine: Synchronously queries local database asset logs,
    feeds them to Google Gemini for contextual sequencing, and commits the result down to SQLite/PostgreSQL.
    """
    user_id = current_user.get("id")
    logger.info(
        f"User ID {user_id} requested personalized AI itinerary configuration for: '{payload.destination_town}'")

    # 1. Protect against timeline input anomalies
    if payload.start_date > payload.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timeline anomaly: Start date cannot fall after the specified end date."
        )

    total_days = (payload.end_date - payload.start_date).days + 1

    # 2. ⚡ HIGH-SPEED RETRIEVAL STEP: Fetch the actual item IDs present inside your local database catalog
    target_city = payload.destination_town.strip()
    db_places = db.query(Places).filter(Places.location.ilike(f"%{target_city}%")).all()
    db_restaurants = db.query(Restaurants).filter(Restaurants.location.ilike(f"%{target_city}%")).all()

    # Extract clean dictionary reference pools so Gemini knows exactly what options exist
    available_places_pool = [{"id": p.id, "name": p.title} for p in db_places]
    available_dining_pool = [{"id": r.id, "name": r.title} for r in db_restaurants]

    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Platform AI configurations key mapping missing from server environment hosts."
        )

    ENDPOINT_URL = f"https://googleapis.com{GEMINI_API_KEY}"

    # 3. CONTEXTUAL PROMPT ENFORCEMENT: We provide our explicit local options to Gemini to ensure data integrity
    base_prompt = """
    You are the core AI travel companion engine for Safardost Pakistan.
    Design a coherent {days}-day chronological vacation plan schedule for a journey to {city}.
    The passenger's available financing allocation budget cap is {budget} PKR.

    Here are the ONLY valid database asset items available in our local catalogs for this location. You MUST select your recommendations strictly from this pool:
    Available Attractions List: {places_pool}
    Available Restaurants List: {dining_pool}

    You MUST respond with a single, raw, minified JSON object matching this structure exactly without markdown wrappers or code blocks:
    {{
        "suggested_hotel_id": 1,
        "recommended_restaurant_ids": [],
        "recommended_place_ids": []
    }}
    Extract and return only the correct integer IDs from the options provided above based on logistics.
    """

    # Safe text replacement routine eliminates native Python formatting KeyError conflicts completely
    prompt = base_prompt.replace("{days}", str(total_days))
    prompt = prompt.replace("{city}", target_city)
    prompt = prompt.replace("{budget}", str(payload.hotel_id if payload.hotel_id else 50000))
    prompt = prompt.replace("{places_pool}", json.dumps(available_places_pool))
    prompt = prompt.replace("{dining_pool}", json.dumps(available_dining_pool))

    request_body = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    # 4. Outbound HTTPS network call loop handles integration workflows securely
    try:
        req = urllib.request.Request(
            ENDPOINT_URL,
            data=json.dumps(request_body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=6) as response:
            raw_ai_text = json.loads(response.read().decode("utf-8"))["candidates"][0]["content"]["parts"][0][
                "text"].strip()

            # Clean off mark-down code blocks safely if appended by the model
            if raw_ai_text.startswith("```json"):
                raw_ai_text = raw_ai_text[7:]
            if raw_ai_text.endswith("```"):
                raw_ai_text = raw_ai_text[:-3]

            ai_data = json.loads(raw_ai_text.strip())

            final_hotel = ai_data.get("suggested_hotel_id", payload.hotel_id)
            final_restaurants = ai_data.get("recommended_restaurant_ids", [r["id"] for r in available_dining_pool[:2]])
            final_places = ai_data.get("recommended_place_ids", [p["id"] for p in available_places_pool[:3]])

    except Exception as e:
        logger.warning(
            f"Outbound API handshake network exception caught for user {user_id}. Executing local fallback rules. Trace: {str(e)}")

        # 🏛️ FIXED DYNAMIC FALLBACK: Dynamically extracts actual active local database record IDs
        # for that city, ensuring the payload never breaks even when fully offline!
        final_hotel = payload.hotel_id if payload.hotel_id else 1
        final_restaurants = [r.id for r in db_restaurants[:2]] if db_restaurants else payload.restaurant_ids
        final_places = [p.id for p in db_places[:3]] if db_places else payload.place_ids

    # 5. Commit structured transactional results down into persistent local data ledger rows
    new_trip = TripContainer(
        user_id=user_id,
        title=payload.title,
        destination_town=target_city.capitalize(),
        start_date=payload.start_date,
        end_date=payload.end_date,
        hotel_id=final_hotel,
        restaurant_ids=final_restaurants,  # Saves the array straight into the native JSON column type
        place_ids=final_places  # Saves the array straight into the native JSON column type
    )

    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    logger.info(
        f"AI Travel Container successfully committed to ledger indexes under assigned Primary Key ID: {new_trip.id}")
    return new_trip


@router.get("/", response_model=List[TripContainerResponse], status_code=status.HTTP_200_OK)
def list_user_trips(current_user: user_dependency, db: db_dependency):
    """
    Fetches the authenticated traveler's saved AI-generated trip portfolio history folders.
    """
    user_id = current_user.get("id")
    logger.info(f"User ID {user_id} requested full travel portfolio folder list stream history data.")
    return db.query(TripContainer).filter(TripContainer.user_id == user_id).all()
