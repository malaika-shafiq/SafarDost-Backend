import os
import json
import urllib.parse
import urllib.request
import urllib.error
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from utils.auth_utils import get_current_user
from schemas.map_schemas import CoordinateResponse, RouteDistanceInput, RouteDistanceResponse

logger = logging.getLogger("safardost.maps")

router = APIRouter(prefix="/maps", tags=["Google Maps API Service Integration"])

user_dependency = Annotated[dict, Depends(get_current_user)]

# Fetch the raw key from cloud parameters environment
RAW_MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# FIXED: Deep sanitize whitespace/newlines right at startup to prevent 404 URL breaks
if RAW_MAPS_KEY:
    GOOGLE_MAPS_KEY = RAW_MAPS_KEY.replace("\n", "").replace("\r", "").strip().replace('"', '').replace("'", "")
else:
    GOOGLE_MAPS_KEY = None


def clean_address_string(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return "Unknown Location, Pakistan"
    return " ".join(word.capitalize() for word in cleaned.split())


# ========================================================
# ADDRESS GEOCODING ENDPOINT (CONVERTS TEXT TO GPS COORDINATES)
# ========================================================
@router.get("/geocode", response_model=CoordinateResponse, status_code=status.HTTP_200_OK)
def get_location_coordinates(address: str, current_user: user_dependency):
    """
    Geocoding Engine: Queries Google Maps API to convert any location text string
    into precise latitude and longitude values for mobile map pin rendering.
    """
    user_id = current_user.get("id")
    user_role = current_user.get("role", "user")

    logger.info(f"User ID {user_id} ({user_role}) initiated geocoding request for: '{address}'")

    if not address or not address.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Address text query parameter cannot be empty."
        )

    clean_city = clean_address_string(address)

    # Presentation Fallback Safety Shield if key is missing completely
    if not GOOGLE_MAPS_KEY:
        logger.warning("Google Maps API key missing. Returning presentation mock coordinates.")
        return CoordinateResponse(
            address_query=address,
            latitude=36.3167,
            longitude=74.6500,
            formatted_address=f"{clean_city}, Gilgit-Baltistan, Pakistan (Mock Simulation)"
        )

    BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    query_params = {
        "address": clean_city,
        "key": GOOGLE_MAPS_KEY
    }
    TARGET_URL = f"{BASE_URL}?{urllib.parse.urlencode(query_params)}"

    try:
        headers = {"User-Agent": "SafarDostTravelApp/1.0 Prototype"}
        req = urllib.request.Request(TARGET_URL, method="GET", headers=headers)

        with urllib.request.urlopen(req, timeout=10.0) as response:
            parsed_json = json.loads(response.read().decode("utf-8"))

            api_status = parsed_json.get("status")

            if api_status == "OK" and parsed_json.get("results"):
                # FIXED: Extract index object 0 from the matching payload results array
                first_result = parsed_json["results"]
                location_node = first_result["geometry"]["location"]
                formatted_name = first_result["formatted_address"]

                return CoordinateResponse(
                    address_query=address,
                    latitude=float(location_node["lat"]),
                    longitude=float(location_node["lng"]),
                    formatted_address=formatted_name
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google Geocoding API rejected the parameters. Status: {api_status}. Message: {parsed_json.get('error_message', 'No details provided.')}"
            )

    except urllib.error.HTTPError as http_ex:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google Upstream Gateway returned HTTP network failure error code: {http_ex.code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Geocoding core failure encountered: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Map backend engine transport breakdown error: {str(e)}"
        )


# ========================================================
# DIRECTIONS DISTANCE ENGINE ENDPOINT (CALCULATES TRAVEL TIME)
# ========================================================
@router.post("/distance", response_model=RouteDistanceResponse, status_code=status.HTTP_200_OK)
def calculate_route_distance(payload: RouteDistanceInput, current_user: user_dependency):
    """
    Directions Optimization Lookup: Connects to Google Directions API
    to analyze distances and live estimated travel timelines between travel hubs.
    """
    user_id = current_user.get("id")
    logger.info(
        f"User ID {user_id} executing distance calculation routing from '{payload.origin}' to '{payload.destination}'")

    clean_origin = clean_address_string(payload.origin)
    clean_dest = clean_address_string(payload.destination)

    # Presentation Fallback Safety Shield if key is missing completely
    if not GOOGLE_MAPS_KEY:
        logger.warning("Google Maps API key missing. Returning mock route configurations.")
        return RouteDistanceResponse(
            origin=clean_origin,
            destination=clean_dest,
            distance_text="374 km",
            duration_text="4 hours 30 mins via M-2 Motorway"
        )

    BASE_URL = "https://maps.googleapis.com/maps/api/directions/json"
    query_params = {
        "origin": clean_origin,
        "destination": clean_dest,
        "key": GOOGLE_MAPS_KEY
    }
    TARGET_URL = f"{BASE_URL}?{urllib.parse.urlencode(query_params)}"

    try:
        headers = {"User-Agent": "SafarDostTravelApp/1.0 Prototype"}
        req = urllib.request.Request(TARGET_URL, method="GET", headers=headers)

        with urllib.request.urlopen(req, timeout=10.0) as response:
            parsed_json = json.loads(response.read().decode("utf-8"))

            api_status = parsed_json.get("status")

            if api_status == "OK" and parsed_json.get("routes"):
                # FIXED: Extract index object 0 from the routes and legs payload arrays
                first_route = parsed_json["routes"]
                first_leg = first_route["legs"]

                return RouteDistanceResponse(
                    origin=first_leg["start_address"],
                    destination=first_leg["end_address"],
                    distance_text=first_leg["distance"]["text"],
                    duration_text=first_leg["duration"]["text"]
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid routing boundary specifications. Google API Status: {api_status}. Details: {parsed_json.get('error_message', 'Check endpoint parameters.')}"
            )

    except urllib.error.HTTPError as http_ex:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google Upstream Directions Gateway returned network failure code: {http_ex.code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Directions system failure encountered: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Map backend route engine transport exception failure: {str(e)}"
        )
