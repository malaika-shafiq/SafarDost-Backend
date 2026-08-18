from fastapi import FastAPI
from database import engine, Base
# 1. Direct specific imports from the main routers root folder
from routers.auth import router as auth_router
from routers.places import router as places_router
from routers.hotels import router as hotels_router
from routers.restaurants import router as restaurants_router
from routers.reviews import router as reviews_router
from routers.bookings import router as bookings_router

# 2. Direct specific imports from the services subfolder
from routers.services.weather import router as weather_router
from routers.services.ai_chat import router as ai_chat_router
from routers.services.trips_planner import router as trips_planner_router
from routers.services.maps import router as maps_router
from dotenv import load_dotenv
load_dotenv()
import os
import uvicorn

if __name__ == "__main__":
    # Railway automatically injects an environment variable named PORT
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)


# Initialize your core app service cleanly
app = FastAPI(
    title="Safardost API Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

Base.metadata.create_all(bind=engine)

@app.get("/")
def first_api():
    return {"Hello": "World"}

app.include_router(auth_router)
app.include_router(places_router)
app.include_router(hotels_router)
app.include_router(restaurants_router)
app.include_router(reviews_router)
app.include_router(bookings_router)
app.include_router(weather_router)
app.include_router(ai_chat_router)
app.include_router(trips_planner_router)
app.include_router(maps_router)



