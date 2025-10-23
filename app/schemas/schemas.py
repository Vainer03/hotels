from pydantic import BaseModel, field_validator, ConfigDict, EmailStr
from typing import Any, Optional, List, TypeVar, Generic, Dict, Any
from decimal import Decimal
from datetime import date, datetime
import enum

from app.core.enums import RoomStatus, BookingStatus

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None

class EmailTaskData(BaseModel):
    to_email: EmailStr
    user_name: str
    booking_data: Dict[str, Any]

class ReportTaskData(BaseModel):
    hotel_id: int
    start_date: date
    end_date: date
    report_type: str

class AnalyticsTaskData(BaseModel):
    hotel_id: Optional[int] = None
    period: str

class HotelBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    city: str
    country: str
    rating: Optional[float] = 0.0

class HotelCreate(HotelBase):
    pass

class HotelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    rating: Optional[float] = None

class HotelRead(HotelBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RoomBase(BaseModel):
    room_number: str
    floor: int
    room_type: str
    description: Optional[str] = None
    price_per_night: float
    capacity: int
    amenities: Optional[str] = None
    status: RoomStatus

class RoomCreate(RoomBase):
    hotel_id: int

class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    floor: Optional[int] = None
    room_type: Optional[str] = None
    description: Optional[str] = None
    price_per_night: Optional[float] = None
    capacity: Optional[int] = None
    amenities: Optional[str] = None
    status: Optional[RoomStatus] = None

class RoomRead(RoomBase):
    id: int
    hotel_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

class UserRead(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BookingBase(BaseModel):
    user_id: int
    hotel_id: int
    room_id: int
    check_in_date: datetime
    check_out_date: datetime
    number_of_guests: int
    special_requests: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    check_in_date: Optional[datetime] = None
    check_out_date: Optional[datetime] = None
    number_of_guests: Optional[int] = None
    special_requests: Optional[str] = None
    status: Optional[BookingStatus] = None

class BookingRead(BookingBase):
    id: int
    booking_reference: str
    total_price: float
    status: BookingStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RoomWithHotelRead(RoomRead):
    hotel: HotelRead

class BookingWithDetailsRead(BookingRead):
    user: UserRead
    hotel: HotelRead
    room: RoomRead
    model_config = ConfigDict(from_attributes=True)

class MessageResponse(BaseModel):
    message: str

class AvailabilitySearch(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    room_type: Optional[str] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    guests: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None