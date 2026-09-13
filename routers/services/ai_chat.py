import os
import math
import json
import requests
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from dotenv import load_dotenv

# Core System Models Injection for Live RAG Lookup Loops
from models.place import Places
from models.hotel import Hotels, HotelRooms
from models.restaurant import Restaurants
from models.tour_package import TourPackages
from models.transport import Transports
from models.user_trip import UserTrips  # 👈 Added tracking model injection
from utils.auth_utils import get_current_user  # 🔒 Security Gate Dependency

from schemas.ai_schemas import ChatRequest, ChatResponse

load_dotenv()

router = APIRouter(prefix="/ai", tags=["LangChain AI Trip Planner Chat Assistant"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "PLACEHOLDER_KEY":
    GEMINI_API_KEY = "AIzaSyYourActualGeminiKeyGoesHere"


# =====================================================================
# 🛠️ INTERNAL DATABASE RETRIEVAL TOOLS
# =====================================================================
def query_travel_database(db: Session, target_module: str, query_filter: str = "") -> str:
    summary = f"Available inventory matching '{query_filter}' inside {target_module}:\n"
    if target_module == "tour_packages":
        packages = db.query(TourPackages).filter(TourPackages.status == "active").all()
        for p in packages:
            summary += f"- Package ID {p.id}: {p.name} | Duration: {p.duration} | Price: PKR {p.price} | Slots Left: {p.available_slots}\n"
    elif target_module == "hotels":
        hotels = db.query(Hotels).filter(Hotels.status == "active").all()
        for h in hotels:
            summary += f"- Hotel ID {h.id}: {h.name} located in Location ID {h.location_id}. Facilities: {h.facilities}\n"
    elif target_module == "places":
        places = db.query(Places).filter(Places.status == "active").all()
        for p in places:
            summary += f"- Spot ID {p.id}: {p.name} | Address: {p.physical_address} | Tips: {p.travel_tips}\n"
    elif target_module == "restaurants":
        restaurants = db.query(Restaurants).filter(Restaurants.status == "active").all()
        for r in restaurants:
            summary += f"- Restaurant ID {r.id}: {r.name} | Cuisine: {r.cuisine} | Timing: {r.opening_information}\n"
    elif target_module == "transports":
        transports = db.query(Transports).filter(Transports.status == "active").all()
        for t in transports:
            summary += f"- Vehicle ID {t.id}: {t.transport_type} running from {t.from_location} to {t.to_location} | Price: {t.price}\n"
    return summary


# =====================================================================
# 6. SYSTEM PROMPT DESIGN & DOMAIN CONSTRAINTS (Strict Guardrails)
# =====================================================================
SYSTEM_AI_PROMPT = """
You are the master AI Travel Assistant for 'Safar Dost', an advanced tourism application for Northern Pakistan.
Your job is to act as a polite conversational travel companion and structure factually grounded trip itineraries.

⚠️ STRICT DOMAIN FILTER GUARDRAIL RULE:
You are EXCLUSIVELY a travel and tourism assistant. You are forbidden from answering any random questions that do not 
relate directly to traveling, vacations, hotels, restaurants, destinations, places, transport fleet arrangements, or route schedules. 
If the user asks about coding, math, general science, politics, historical events unrelated to tourism, or any other random topic, 
you must politely decline to answer. For example, respond with: 'I can only assist you with travel-related queries for Safar Dost. Let's plan your next adventure!'

INVENTORY CONTROLS:
1. You must ONLY recommend items that exist inside the local database using your available data context rows.
2. If the user is just saying hello or asking casual travel questions, chat warmly and keep 'show_plan_button' as false.
3. If the user explicitly asks for a trip plan or itinerary generation, you MUST structure a plan using real database rows. 
   You must flip 'show_plan_button' to true, and populate 'meta_plan_data' with a clean JSON payload mapping the destination, 
   duration days count, and a highly detailed day-by-day itinerary breakdowns description string text that the frontend can save to the user's dashboard records.

Always speak confidently and helpfully about Pakistan's northern tourist tracks.
"""


# =====================================================================
# 7. THE CORE CHAT EXECUTION ENDPOINT (🔒 Authenticated Users)
# =====================================================================
@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def converse_with_trip_planner_assistant(
        chat_request: ChatRequest,
        current_user: user_dependency,
        db: db_dependency
):
    try:
        user_input = chat_request.message.strip()
        user_display_name = current_user.get("first_name", "Traveler")

        # 1. ORCHESTRATE INTENT LOOKUPS
        database_context = ""
        planning_keywords = ["plan", "trip", "itinerary", "hotel", "restaurant", "transport", "package", "tour"]

        if any(keyword in user_input.lower() for keyword in planning_keywords):
            database_context += query_travel_database(db, "places")
            database_context += query_travel_database(db, "hotels")
            database_context += query_travel_database(db, "restaurants")
            database_context += query_travel_database(db, "tour_packages")
            database_context += query_travel_database(db, "transports")

        # 2. BUNDLE PAYLOAD FOR STRUCTURED GENERATION
        composite_prompt = f"""
        System Context: {SYSTEM_AI_PROMPT}
        Traveler Identity Context: The current logged-in user's name is {user_display_name}. Address them politely when greeting them.
        Live Database Rows Available: {database_context}
        User Traveler Message: {user_input}

        Provide your final response as a clean, valid JSON object matching these exact keys:
        {{
           "bot_response": "your conversational text or domain rejection here",
           "show_plan_button": true or false,
           "meta_plan_data": null or {{ 
                "destination": "string", 
                "days": int, 
                "estimated_cost": float,
                "itinerary_details": "Highly detailed day-by-day text itinerary text to write to disk ledger"
           }}
        }}
        Ensure you only return the raw JSON object string with no markdown formatting. Do not wrap the JSON output in backticks.
        """

        # 3. DIRECT HTTP REST API CALL TO THE OFFICIAL PUBLIC ENDPOINT
        url = f"https://googleapis.com{GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": composite_prompt}]
            }]
        }

        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Google API authentication handshake failed.")

        # 4. PARSE OUTPUT TO SCHEMA CONTRACT Safely
        try:
            response_json = response.json()
            ai_text = response_json["candidates"]["content"]["parts"]["text"].strip()

            clean_json_text = ai_text.replace("```json", "").replace("```", "").strip("`").strip()
            parsed_json = json.loads(clean_json_text)

            return ChatResponse(
                bot_response=parsed_json.get("bot_response", "I can help you plan your travel across Pakistan!"),
                show_plan_button=parsed_json.get("show_plan_button", False),
                meta_plan_data=parsed_json.get("meta_plan_data")
            )
        except Exception:
            return ChatResponse(
                bot_response=response.text.strip(),
                show_plan_button=False,
                meta_plan_data=None
            )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Engine Direct API Request Failure: {str(error)}"
        )
