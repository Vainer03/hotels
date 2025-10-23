from .hotels import router as hotels_router
from .rooms import router as rooms_router
from .users import router as users_router
from .bookings import router as bookings_router

__all__ = ["hotels_router", "rooms_router", "users_router", "bookings_router"]