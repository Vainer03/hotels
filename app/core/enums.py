import enum

class RoomStatus(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied" 
    MAINTENANCE = "maintenance"
    CLEANING = "cleaning"
    INACTIVE = "inactive"

class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"