from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.core.enums import RoomStatus, BookingStatus, UserRole

class Hotel(Base):
    __tablename__ = "hotels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(200), nullable=False)
    city = Column(String(50), nullable=False)
    country = Column(String(50), nullable=False)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    rooms = relationship(
        "Room", 
        back_populates="hotel", 
        cascade="all, delete-orphan",
        passive_deletes=True,
        )
    
    bookings = relationship(
        "Booking", 
        back_populates="hotel",
        cascade="all, delete-orphan",
        passive_deletes=True,
        )

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)
    room_number = Column(String(10), nullable=False)
    floor = Column(Integer, nullable=False)
    room_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    price_per_night = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)
    amenities = Column(Text, nullable=True)
    status = Column(Enum(RoomStatus), default=RoomStatus.AVAILABLE)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    hotel = relationship("Hotel", back_populates="rooms")
    bookings = relationship(
        "Booking", 
        back_populates="room",
        )

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bookings = relationship(
        "Booking", 
        back_populates="user",
        )

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"))
    hotel_id = Column(Integer, ForeignKey("hotels.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    number_of_guests = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.CONFIRMED)
    special_requests = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="bookings")
    hotel = relationship("Hotel", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")