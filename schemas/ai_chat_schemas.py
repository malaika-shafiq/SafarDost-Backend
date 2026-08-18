from pydantic import BaseModel, Field

class AIChatRequest(BaseModel):
    user_message: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        examples=["What should I pack for Hunza in October?"],
        description="The raw open-ended question string submitted by the traveler client"
    )

class AIChatResponse(BaseModel):
    assistant_reply: str = Field(..., description="The contextually generated response text string from the AI agent")
    timestamp_utc: str = Field(..., description="The execution tracking timestamp")
