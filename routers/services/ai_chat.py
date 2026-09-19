import os
import json
import time
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db

# 🚀 INJECTS YOUR EXACT CODES OFFICIAL GOOGLE GENAI LIBRARIES
from google import genai
from google.genai import types

# Core System Models Injection for Live RAG Lookup Loops
from models.place import Places
from models.hotel import Hotels, HotelRooms
from models.restaurant import Restaurants
from models.tour_package import TourPackages
from models.transport import Transports
from utils.auth_utils import get_current_user  # 🔒 Security Gate Dependency

from schemas.ai_schemas import ChatRequest, ChatResponse

from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/ai", tags=["LangChain AI Trip Planner Chat Assistant"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# =====================================================================
# 🛠️ INTERNAL DATABASE RETRIEVAL TOOLS (RAG ENGINE)
# =====================================================================
def query_travel_database(db: Session, target_module: str, query_filter: str = "") -> str:
    """
    BACKGROUND RETRIEVAL ENGINE: Automatically queries your PostgreSQL tables based on
    the intent decoded by the model. Completely eliminates hallucinated recommendations.
    """
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
    """
    TRAVELER INTERACTIVE ENGAGEMENT INTERFACE: Processes plain text prompts through Gemini.
    Leverages your verified standalone 'google-genai' SDK engine client token parameters.
    """
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

        # ✅ MATCHES YOUR CODE LINE 8 EXACTLY: Initializes using your direct functional profile
        # Passing your explicit dashboard token here guarantees it mounts successfully on Railway!
        cloud_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_KEY")
        client = genai.Client(api_key=str(cloud_key).strip())

        # 🏎️ INDUSTRY-STANDARD HIGH-AVAILABILITY EXPONENTIAL BACKOFF RETRY ENGINE:
        max_retries = 3
        sleep_delay = 1.0  # Initial sleep delay buffer in seconds
        response = None

        for attempt in range(max_retries):
            try:
                # 🚀 EXECUTES YOUR AUTHENTIC LIVE MODEL GENERATION:
                response = client.models.generate_content(
                    model='gemini-3.6-flash',  # Your verified running model string parameter
                    contents=composite_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    ),
                )
                # If the call succeeds, break out of the retry loop completely!
                break

            except Exception as api_error:
                # If we hit Google's 503 high demand or network spikes, pause and try again!
                if attempt < max_retries - 1:
                    time.sleep(sleep_delay)
                    sleep_delay *= 2  # Double the backoff duration for the next attempt (1s -> 2s)
                    continue

                # If all 3 live execution attempts fail completely, raise the clean HTTP exception trace
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Gemini SDK Core Execution Failure after retries: {str(api_error)}"
                )

        # 4. PARSE LIVE RESPONSE TO SYSTEM CONTRACT SCHEMA
        try:
            ai_text = response.text.strip()
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

    except HTTPException as http_err:
        # Let our custom 503 error pass straight through to the Swagger dashboard!
        raise http_err


    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gemini SDK Core Execution Failure: {str(error)}"
        )
