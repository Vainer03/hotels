from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
import app.models.hotels as models
import app.schemas.schemas as schemas
import app.core.enums as enums
from app.database import get_db
from app.services.cache_service import CacheService
from app.core.dependencies import require_admin

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.get("/", response_model=List[schemas.RoomRead])
async def get_rooms(
    skip: int = 0,
    limit: int = 100,
    hotel_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Получить список комнат с кэшированием"""
    cache_service = CacheService()
    
    cache_key = f"rooms:skip:{skip}:limit:{limit}:hotel_id:{hotel_id}"
    cached_result = await cache_service.get_cached_rooms({"cache_key": cache_key})
    
    if cached_result:
        return cached_result
    
    query = db.query(models.Room)
    
    if hotel_id:
        query = query.filter(models.Room.hotel_id == hotel_id)
    
    rooms = query.offset(skip).limit(limit).all()
    
    rooms_data = [schemas.RoomRead.model_validate(room).model_dump() for room in rooms]
    
    await cache_service.cache_available_rooms(
        {"cache_key": cache_key}, 
        rooms_data, 
        expire=300
    )
    
    return rooms

@router.get("/available", response_model=List[schemas.RoomRead])
async def get_available_rooms(
    hotel_id: int,
    check_in_date: date,
    check_out_date: date,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Найти доступные комнаты в отеле на указанные даты с кэшированием"""
    cache_service = CacheService()
    
    search_params = {
        "hotel_id": hotel_id,
        "check_in_date": check_in_date.isoformat(),
        "check_out_date": check_out_date.isoformat(),
        "min_price": min_price,
        "max_price": max_price
    }
    
    cached_rooms = await cache_service.get_cached_rooms(search_params)
    if cached_rooms:
        return cached_rooms
    
    if check_in_date >= check_out_date:
        raise HTTPException(
            status_code=400,
            detail="Дата выезда должна быть позже даты заезда"
        )
    
    if check_in_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="Дата заезда не может быть в прошлом"
        )
    
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Отель не найден")
    
    query = db.query(models.Room).filter(
        models.Room.hotel_id == hotel_id,
        models.Room.status == models.RoomStatus.AVAILABLE
    )
    
    if min_price is not None:
        query = query.filter(models.Room.price_per_night >= min_price)
    if max_price is not None:
        query = query.filter(models.Room.price_per_night <= max_price)
    
    all_rooms = query.all()
    
    available_rooms = []
    for room in all_rooms:
        conflicting_booking = db.query(models.Booking).filter(
            models.Booking.room_id == room.id,
            models.Booking.status.in_([models.BookingStatus.CONFIRMED, models.BookingStatus.CHECKED_IN]),
            models.Booking.check_in_date < check_out_date,
            models.Booking.check_out_date > check_in_date
        ).first()
        
        if not conflicting_booking:
            available_rooms.append(room)
    
    rooms_data = [schemas.RoomRead.model_validate(room).model_dump() for room in available_rooms]
    
    await cache_service.cache_available_rooms(search_params, rooms_data)
    
    return available_rooms

@router.get("/search/available", response_model=List[schemas.RoomWithHotelRead])
async def search_available_rooms(
    city: Optional[str] = None,
    country: Optional[str] = None,
    room_type: Optional[str] = None,
    check_in: Optional[datetime] = None,
    check_out: Optional[datetime] = None,
    guests: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Поиск доступных комнат с фильтрами"""
    try:
        print(f"🔍 Поиск комнат: city={city}, check_in={check_in}, check_out={check_out}")
        
        query = db.query(models.Room).join(models.Hotel)
        
        if city:
            query = query.filter(models.Hotel.city.ilike(f"%{city}%"))
        if country:
            query = query.filter(models.Hotel.country.ilike(f"%{country}%"))
        
        if room_type:
            query = query.filter(models.Room.room_type.ilike(f"%{room_type}%"))
        if guests:
            query = query.filter(models.Room.capacity >= guests)
        if min_price is not None:
            query = query.filter(models.Room.price_per_night >= min_price)
        if max_price is not None:
            query = query.filter(models.Room.price_per_night <= max_price)
        
        query = query.filter(models.Room.status == "available")
        
        if check_in and check_out:
            if check_in >= check_out:
                raise HTTPException(
                    status_code=400,
                    detail="Дата выезда должна быть позже даты заезда"
                )
            
            booked_rooms_subquery = db.query(models.Booking.room_id).filter(
                models.Booking.status.in_(["confirmed", "checked_in"]),
                models.Booking.check_in_date < check_out,
                models.Booking.check_out_date > check_in
            ).subquery()
            
            query = query.filter(~models.Room.id.in_(booked_rooms_subquery))
        
        available_rooms = query.all()
        
        print(f"Найдено {len(available_rooms)} доступных комнат")
        
        return available_rooms
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при поиске комнат: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при поиске комнат: {str(e)}"
        )

@router.get("/{room_id}", response_model=schemas.RoomWithHotelRead)
async def get_room(room_id: int, db: Session = Depends(get_db)):
    """Получить комнату по ID"""
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    return room

@router.post("/", response_model=schemas.RoomRead)
async def create_room(
    room: schemas.RoomCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)):
    """Создать новую комнату"""
    hotel = db.query(models.Hotel).filter(models.Hotel.id == room.hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Отель не найден")
    
    existing_room = db.query(models.Room).filter(
        models.Room.hotel_id == room.hotel_id,
        models.Room.room_number == room.room_number
    ).first()
    
    if existing_room:
        raise HTTPException(
            status_code=400,
            detail="Комната с таким номером уже существует в этом отеле"
        )
    
    db_room = models.Room(**room.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    
    cache_service = CacheService()
    await cache_service.invalidate_hotel_cache(room.hotel_id)
    
    return db_room

@router.put("/{room_id}", response_model=schemas.RoomRead)
async def update_room(
    room_id: int,
    room_update: schemas.RoomUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Обновить информацию о комнате"""
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    
    if room_update.room_number and room_update.room_number != room.room_number:
        existing_room = db.query(models.Room).filter(
            models.Room.hotel_id == room.hotel_id,
            models.Room.room_number == room_update.room_number
        ).first()
        if existing_room:
            raise HTTPException(
                status_code=400,
                detail="Комната с таким номером уже существует в этом отеле"
            )
    
    update_data = room_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(room, field, value)
    
    db.commit()
    db.refresh(room)
    
    cache_service = CacheService()
    await cache_service.invalidate_hotel_cache(room.hotel_id)
    
    return room

@router.put("/{room_id}/status", response_model=schemas.MessageResponse)
async def update_room_status(
    room_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Обновить статус комнаты"""
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    
    valid_statuses = ["available", "occupied", "maintenance", "cleaning"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Неверный статус. Допустимые значения: {', '.join(valid_statuses)}"
        )
    
    room.status = status
    db.commit()
    
    return {"message": f"Статус комнаты обновлен на {status}"}


@router.delete("/{room_id}", response_model=schemas.MessageResponse)
def delete_room(
    room_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)):
    """Удалить комнату с обработкой активных бронирований"""
    try:
        db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
        if not db_room:
            raise HTTPException(status_code=404, detail="Комната не найдена")
        
        room_number = db_room.room_number
        hotel_id = db_room.hotel_id
        
        all_bookings = db.query(models.Booking).filter(
            models.Booking.room_id == room_id
        ).all()
        
        current_time = datetime.now()
        active_bookings = []
        
        for booking in all_bookings:
            if booking.status in ["confirmed", "checked_in"]:
                booking.status = "cancelled"
                booking.cancellation_reason = f"Комната #{room_number} удалена из системы"
                booking.cancelled_at = current_time
                active_bookings.append(booking)
                print(f"Cancelled booking {booking.id}")
        
        print(f"Cancelled {len(active_bookings)} active bookings for room {room_id}")
        
        db.delete(db_room)
        db.commit()
        
        try:
            cache_service = CacheService()
            cache_service.invalidate_room_cache(room_id)
            cache_service.invalidate_hotel_cache(hotel_id)
            cache_service.invalidate_pattern("rooms_search:*")
            cache_service.invalidate_pattern(f"hotel_rooms:{hotel_id}:*")
        except Exception as cache_error:
            print(f"Cache error: {cache_error}")
        
        return {
            "message": f"Комната {room_number} успешно удалена",
            "details": {
                "room_id": room_id,
                "cancelled_active_bookings": len(active_bookings),
                "preserved_completed_bookings": len(all_bookings) - len(active_bookings),
                "cancelled_booking_ids": [b.id for b in active_bookings]
            }
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error deleting room {room_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении комнаты: {str(e)}")