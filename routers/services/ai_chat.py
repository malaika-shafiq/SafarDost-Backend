import os
import json
import logging
import datetime
import urllib.request
import urllib.parse
import urllib.error
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from utils.auth_utils import get_current_user
from schemas.ai_chat_schemas import AIChatRequest, AIChatResponse

logger = logging.getLogger("safardost.ai_chat")

router = APIRouter(prefix="/ai-chat", tags=["Safardost AI Conversational Assistant Portal"])

user_dependency = Annotated[dict, Depends(get_current_user)]

# Fetch raw key string from environment host configurations
RAW_GEMINI_KEY = os.getenv("GOOGLE_GEMINI_KEY")

# Deep sanitize whitespace and quotes at startup to prevent endpoint corruption
if RAW_GEMINI_KEY:
    GEMINI_API_KEY = RAW_GEMINI_KEY.replace("\n", "").replace("\r", "").strip().replace('"', '').replace("'", "")
else:
    GEMINI_API_KEY = None


@router.post("/message", response_model=AIChatResponse, status_code=status.HTTP_200_OK)
def converse_with_travel_assistant(payload: AIChatRequest, current_user: user_dependency):
    """
    AI Travel Concierge Portal: Creates a direct, secure conversational channel to Google Gemini.
    Enforces a strict native system instruction framework to bind the AI to a Pakistani travel expert persona.
    """
    user_id = current_user.get("id")
    raw_message = payload.user_message.strip()
    logger.info(f"User ID {user_id} dispatched portal assistant message: '{raw_message}'")

    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Platform AI configuration credentials missing from system host environments."
        )

    if not raw_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User message query parameter text cannot be empty."
        )

    # Clean URL construction using a parameter mapping dictionary to protect the domain path
    BASE_URL = "https://googleapis.com"
    query_params = {"key": GEMINI_API_KEY}
    ENDPOINT_URL = f"{BASE_URL}?{urllib.parse.urlencode(query_params)}"

    # SYSTEM GUARDRAIL: Grounding prompt rules
    system_instruction = (
        "You are Safardost AI, an elite, interactive conversational travel concierge embedded inside the Safardost mobile application. "
        "Your sole purpose is to assist users with traveling, packing, logistics, route status, food, culture, and safety within Pakistan. "
        "[STRICT OPERATIONAL CONSTRAINT] If the user asks a question completely unrelated to travel, hotels, transport, or geography in Pakistan "
        "(such as writing software code, solving mathematics equations, or translating non-travel texts), politely reject the request. "
        "Respond EXACTLY with: 'I am your Safardost Travel Assistant, dedicated exclusively to guiding your journeys across Pakistan. "
        "Please ask me any question regarding destinations, packing, route updates, or local culture!' "
        "Keep your responses actionable, warm, polite, and formatted beautifully for a smartphone chat window screen."
    )

    # Build the official Gemini payload structure
    request_body = {
        "contents": [{
            "parts": [{"text": raw_message}]
        }],
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        }
    }

    try:
        req = urllib.request.Request(
            ENDPOINT_URL,
            data=json.dumps(request_body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=12.0) as response:
            raw_response = response.read().decode("utf-8")
            response_json = json.loads(raw_response)

            # Extract out response tokens safely
            ai_reply_text = response_json["candidates"][0]["content"]["parts"][0]["text"].strip()

            return AIChatResponse(
                assistant_reply=ai_reply_text,
                timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )

    except urllib.error.HTTPError as http_ex:
        error_content = http_ex.read().decode("utf-8")
        logger.error(f"Gemini API Gateway rejected request (Status {http_ex.code}): {error_content}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini Upstream Platform rejected call parameters (Status {http_ex.code}): {error_content[:150]}"
        )
    except Exception as e:
        masked_key = f"{GEMINI_API_KEY[:4]}... (Length: {len(GEMINI_API_KEY)})" if GEMINI_API_KEY else "Empty"
        logger.error(f"Live Gemini connection pipeline failure: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Live AI backend connection error: {str(e)}. "
                f"Verify your GOOGLE_GEMINI_KEY variable values in Railway settings. "
                f"Server is currently parsing key as: {masked_key}"
            )
        )
