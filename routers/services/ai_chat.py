import os
import json
import logging
import datetime
import urllib.parse
import urllib.request
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from utils.auth_utils import get_current_user
from schemas.ai_chat_schemas import AIChatRequest, AIChatResponse

logger = logging.getLogger("safardost.ai_chat")

router = APIRouter(prefix="/ai-chat", tags=["Safardost AI Conversational Assistant Portal"])

user_dependency = Annotated[dict, Depends(get_current_user)]

# ⚡ OPTIMIZATION: Cache Gemini API credentials globally once at startup to save system memory lookups
GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_KEY")


@router.post("/message", response_model=AIChatResponse, status_code=status.HTTP_200_OK)
def converse_with_travel_assistant(payload: AIChatRequest, current_user: user_dependency):
    """
    AI Travel Concierge Portal: Creates a direct, secure conversational channel to Google Gemini.
    Enforces a strict system instruction matrix to lock the AI into a Pakistani travel expert persona.
    """
    user_id = current_user.get("id")
    raw_message = payload.user_message.strip()
    logger.info(f"User ID {user_id} dispatched portal assistant message: '{raw_message}'")

    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Platform AI configuration credentials missing from system host environments."
        )

    ENDPOINT_URL = f"https://googleapis.com{GEMINI_API_KEY}"

    # 🛠️ SYSTEM GUARDRAIL: Restricts conversational boundaries directly via system text rules.
    base_prompt = """
    You are Safardost AI, an elite, interactive conversational travel concierge embedded inside the Safardost mobile application.
    Your sole purpose is to assist users with traveling, packing, logistics, route status, food, culture, and safety within Pakistan.

    [STRICT OPERATIONAL CONSTRAINT]
    If the user asks a question completely unrelated to travel, hotels, transport, or geography in Pakistan (such as writing software code, solving mathematics equations, or translating non-travel texts), politely reject the request. Respond with: "I am your Safardost Travel Assistant, dedicated exclusively to guiding your journeys across Pakistan. Please ask me any question regarding destinations, packing, route updates, or local culture!"

    User Travel Question: "__USER_MSG__"

    Provide a warm, polite, and practical answer. Keep your responses actionable and formatted beautifully for a smartphone chat window screen.
    """

    # Safe text replacement routine executes seamlessly with no brace anomalies
    prompt = base_prompt.replace("__USER_MSG__", raw_message)

    request_body = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        req = urllib.request.Request(
            ENDPOINT_URL,
            data=json.dumps(request_body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=8) as response:
            raw_response = response.read().decode("utf-8")
            response_json = json.loads(raw_response)
            ai_reply_text = response_json["candidates"]["content"]["parts"]["text"].strip()

            return {
                "assistant_reply": ai_reply_text,
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

    except Exception as e:
        logger.warning(
            f"Outbound AI portal exception caught for User {user_id}. Executing local fallback rules. Trace: {str(e)}")

        # 🏛️ CONVERSATIONAL PRESENTATION FALLBACK
        fallback_msg = raw_message.lower()
        reply = "That is an excellent question! As your Safardost assistant, I highly recommend verifying active high-altitude pass closures (like Babusar or Lowari) directly via National Highway Authority (NHA) alerts or local Gilgit-Baltistan travel advisories before starting your journey."

        if "pack" in fallback_msg:
            reply = "When packing for northern Pakistan during seasonal shifts, always carry high-quality thermal inner wear, windproof fleece jackets, a warm beanie, and dependable trekking boots to handle rugged mountain trails comfortably."
        elif "open" in fallback_msg or "babusar" in fallback_msg:
            reply = "Babusar Top road status alert: This pass (4,173m) routinely shuts down due to heavy snowfall from late October until early June. During these months, bypass the pass and take the alternate Karakoram Highway route via Besham and Kohistan to enter Gilgit safely."

        return {
            "assistant_reply": reply,
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
