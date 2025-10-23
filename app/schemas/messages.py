from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class BookingEventType(str, Enum):
    CREATED = "booking.created"
    UPDATED = "booking.updated"
    CANCELLED = "booking.cancelled"
    CHECKED_IN = "booking.checked_in"
    CHECKED_OUT = "booking.checked_out"

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class BookingEvent(BaseModel):
    event_type: BookingEventType
    booking_id: int
    user_id: int
    hotel_id: int
    room_id: int
    check_in_date: datetime
    check_out_date: datetime
    total_price: float
    timestamp: datetime = datetime.utcnow()
    metadata: Optional[dict] = None

class NotificationMessage(BaseModel):
    notification_type: NotificationType
    recipient: str
    subject: str
    message: str
    template_id: Optional[str] = None
    metadata: Optional[dict] = None

class RoomStatusEvent(BaseModel):
    room_id: int
    hotel_id: int
    old_status: str
    new_status: str
    reason: str
    timestamp: datetime = datetime.utcnow()