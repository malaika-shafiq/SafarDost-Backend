from database import Base  # Crucial: Import the central Base class first

# 🏛️ EXPLICIT RELATIVE IMPORTS: The dot (.) forces Python to look inside this exact folder!
from .user import Users
from .hotel import Hotels, HotelRooms
from .restaurant import Restaurants
from .place import Places
from .review import Reviews
from .booking import Bookings
from .store import GearItem, GearOrder
from .category import Categories
from .location import Locations
from .image import Images
from .user_trip import UserTrips
from .weather import WeatherCache
from .transport import Transports
from .tour_package import TourPackages