# tests/conftest.py
import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Добавляем путь к корневой папке в Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import get_db, Base
from app.core.enums import RoomStatus, BookingStatus

# Тестовая база данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    # Создаем таблицы для каждого теста
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    # Очищаем после теста
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_hotel_data():
    return {
        "name": "Grand Hotel",
        "description": "Luxury hotel in city center",
        "address": "123 Main St",
        "city": "Moscow",
        "country": "Russia",
        "rating": 4.5
    }

@pytest.fixture
def sample_room_data():
    return {
        "room_number": "101",
        "floor": 1,
        "room_type": "Standard",
        "description": "Comfortable standard room",
        "price_per_night": 100.0,
        "capacity": 2,
        "amenities": "WiFi, TV, AC",
        "status": RoomStatus.AVAILABLE.value,  # Используем значение enum
        "hotel_id": 1,
    }

@pytest.fixture
def sample_user_data():
    return {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890"
    }

@pytest.fixture
def room_status_available():
    return "AVAILABLE"

@pytest.fixture
def room_status_occupied():
    return "OCCUPIED"

@pytest.fixture
def booking_status_confirmed():
    return BookingStatus.CONFIRMED.value