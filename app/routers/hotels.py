from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import app.models.hotels as models
import app.schemas.schemas as schemas
from app.database import get_db
from app.services.cache_service import CacheService

router = APIRouter(prefix="/hotels", tags=["hotels"])

@router.get("/", response_model=List[schemas.HotelRead])
async def get_hotels(
    skip: int = 0,
    limit: int = 100,
    city: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получить список отелей с кэшированием"""
    cache_service = CacheService()
    
    cache_key = f"hotels:skip:{skip}:limit:{limit}:city:{city}:country:{country}"
    cached_result = await cache_service.get_cached_rooms({"cache_key": cache_key})
    
    if cached_result:
        return cached_result
    
    """Получить список отелей с фильтрацией"""
    print("GET /hotels/ request received")
    
    try:
        query = db.query(models.Hotel)
        
        if city:
            query = query.filter(models.Hotel.city == city)
        if country:
            query = query.filter(models.Hotel.country == country)
        
        hotels = query.offset(skip).limit(limit).all()
        
        if not hotels:
            return []
        
        result = []
        for hotel in hotels:
            try:
                hotel_read = schemas.HotelRead.model_validate(hotel)
                result.append(hotel_read)
            except Exception as conv_error:
                print(f"Error converting hotel {hotel.id}: {conv_error}")
                print(f"Hotel data: {hotel.__dict__}")
                raise conv_error
        
        hotels_data = [schemas.HotelRead.model_validate(hotel).model_dump() for hotel in hotels]
        await cache_service.cache_available_rooms(
            {"cache_key": cache_key}, 
            hotels_data, 
            expire=300 
        )
        
        return result
        
    except Exception as e:
        print(f"CRITICAL ERROR in get_hotels: {str(e)}")
        import traceback
        print("Stack trace:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка при получении отелей: {str(e)}")

@router.get("/{hotel_id}", response_model=schemas.HotelRead)
async def get_hotel(hotel_id: int, db: Session = Depends(get_db)):
    """Получить отель по ID с кэшированием"""
    cache_service = CacheService()
    
    cached_hotel = await cache_service.get_cached_hotel(hotel_id)
    if cached_hotel:
        return cached_hotel
    
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Отель не найден")
    
    hotel_data = schemas.HotelRead.model_validate(hotel)
    
    await cache_service.cache_hotel(hotel_id, hotel_data.model_dump())
    
    return hotel_data

@router.post("/", response_model=schemas.HotelRead)
async def create_hotel(hotel: schemas.HotelCreate, db: Session = Depends(get_db)):
    """Создать новый отель"""
    print(f"Received hotel data: {hotel.model_dump()}")
    
    try:
        db_hotel = models.Hotel(**hotel.model_dump())
        db.add(db_hotel)
        db.commit()
        db.refresh(db_hotel)
        print(f"Hotel created successfully: {db_hotel.id}")
        
        cache_service = CacheService()
        await cache_service.invalidate_hotel_cache(db_hotel.id)
        
        return db_hotel
    except Exception as e:
        db.rollback()
        print(f"Error creating hotel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании отеля: {str(e)}")

@router.put("/{hotel_id}", response_model=schemas.HotelRead)
async def update_hotel(
    hotel_id: int, 
    hotel_update: schemas.HotelUpdate, 
    db: Session = Depends(get_db)
):
    """Обновить информацию об отеле"""
    db_hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()
    if not db_hotel:
        raise HTTPException(status_code=404, detail="Отель не найден")
    
    update_data = hotel_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_hotel, field, value)
    
    db.commit()
    db.refresh(db_hotel)
    
    cache_service = CacheService()
    await cache_service.invalidate_hotel_cache(hotel_id)
    
    return db_hotel

@router.delete("/{hotel_id}", response_model=schemas.MessageResponse)
def delete_hotel(hotel_id: int, db: Session = Depends(get_db)):
    """Удалить отель (активные бронирования становятся неактивными)"""
    try:
        db_hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()
        if not db_hotel:
            raise HTTPException(status_code=404, detail="Отель не найден")
        
        direct_bookings = db.query(models.Booking).filter(
            models.Booking.hotel_id == hotel_id
        ).all()
        
        room_bookings = db.query(models.Booking).filter(
            models.Booking.room_id.in_(
                db.query(models.Room.id).filter(models.Room.hotel_id == hotel_id)
            )
        ).all()
        
        all_bookings = direct_bookings + room_bookings
        
        active_bookings_updated = 0
        cancelled_bookings = []
        
        for booking in all_bookings:
            if booking.status in ["confirmed", "checked_in"]:
                cancelled_bookings.append({
                    "id": booking.id,
                    "user_id": booking.user_id,
                    "room_id": booking.room_id,
                    "original_status": booking.status,
                    "check_in_date": booking.check_in_date,
                    "check_out_date": booking.check_out_date
                })
                
                booking.status = "cancelled"
                booking.cancellation_reason = "Отель удален из системы"
                booking.cancelled_at = func.now()
                active_bookings_updated += 1
        
        print(f"Marked {active_bookings_updated} active bookings as cancelled for hotel {hotel_id}")
        
        rooms_updated = db.query(models.Room).filter(
            models.Room.hotel_id == hotel_id
        ).update({
            "status": "inactive"
        })
        
        print(f"Marked {rooms_updated} rooms as inactive for hotel {hotel_id}")
        
        hotel_name = db_hotel.name
        db.delete(db_hotel)
        db.commit()
        
        try:
            cache_service = CacheService()
            cache_service.invalidate_hotel_cache(hotel_id)
        except Exception as cache_error:
            print(f"Cache error: {cache_error}")
        
        return {
            "message": f"Отель '{hotel_name}' успешно удален",
            "hotel_id": hotel_id,
            "inactive_rooms": rooms_updated,
            "cancelled_bookings": active_bookings_updated,
            "cancellation_details": cancelled_bookings
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error deleting hotel {hotel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении отеля")