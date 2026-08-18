from database import Base  # Crucial: Import the central Base class first

# 🏛️ EXPLICIT RELATIVE IMPORTS: The dot (.) forces Python to look inside this exact folder!
from .user import Users
from .hotel import Hotels
from .restaurant import Restaurants
from .place import Places
from .review import Reviews
from .booking import HotelBookings, RestaurantBookings, TransportBookings
from .store import GearItem, GearOrder
