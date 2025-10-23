from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import app.models.hotels as models
import app.schemas.schemas as schemas
from app.database import get_db
from app.services.booking_events import BookingEventService
from app.services.notification_service import NotificationService
from app.services.cache_service import CacheService

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("/", response_model=schemas.BookingRead)
async def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    """Создать новое бронирование"""
    user = db.query(models.User).filter(models.User.id == booking.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    hotel = db.query(models.Hotel).filter(models.Hotel.id == booking.hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Отель не найден")
    
    room = db.query(models.Room).filter(models.Room.id == booking.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    
    if room.hotel_id != booking.hotel_id:
        raise HTTPException(
            status_code=400,
            detail="Комната не принадлежит указанному отелю"
        )
    
    if room.status != models.RoomStatus.AVAILABLE:
        raise HTTPException(
            status_code=400,
            detail="Комната недоступна для бронирования"
        )
    
    if booking.number_of_guests > room.capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Комната вмещает максимум {room.capacity} гостей"
        )
    
    if booking.check_in_date >= booking.check_out_date:
        raise HTTPException(
            status_code=400,
            detail="Дата выезда должна быть позже даты заезда"
        )
    
    existing_booking = db.query(models.Booking).filter(
        models.Booking.room_id == booking.room_id,
        models.Booking.status.in_([models.BookingStatus.CONFIRMED, models.BookingStatus.CHECKED_IN]),
        models.Booking.check_in_date < booking.check_out_date,
        models.Booking.check_out_date > booking.check_in_date
    ).first()
    
    if existing_booking:
        raise HTTPException(
            status_code=400,
            detail="Комната уже забронирована на указанные даты"
        )
    
    nights = (booking.check_out_date - booking.check_in_date).days
    total_price = nights * room.price_per_night
    
    db_booking = models.Booking(
        **booking.model_dump(),
        total_price=total_price
    )
    
    room.status = models.RoomStatus.OCCUPIED
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    try:
        event_service = BookingEventService()
        notification_service = NotificationService()
        cache_service = CacheService()
        
        booking_data = {
            "id": db_booking.id,
            "user_id": db_booking.user_id,
            "hotel_id": db_booking.hotel_id,
            "room_id": db_booking.room_id,
            "check_in_date": db_booking.check_in_date.isoformat(),
            "check_out_date": db_booking.check_out_date.isoformat(),
            "total_price": db_booking.total_price,
            "booking_reference": db_booking.booking_reference,
            "number_of_guests": db_booking.number_of_guests
        }
        
        await event_service.publish_booking_created(booking_data)
        
        await notification_service.send_booking_confirmation(
            user_email=user.email,
            user_name=f"{user.first_name} {user.last_name}",
            booking_data={
                **booking_data,
                "hotel_name": hotel.name,
                "room_number": room.room_number
            }
        )
        
        await cache_service.track_booking_stats(hotel.id, room.id)
        
        await cache_service.invalidate_user_cache(user.id)
        await cache_service.invalidate_hotel_cache(hotel.id)
        
    except Exception as e:
        print(f"Failed to publish booking event: {e}")
    
    return db_booking

@router.get("/", response_model=List[schemas.BookingWithDetailsRead])
async def get_bookings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список всех бронирований"""
    return db.query(models.Booking).offset(skip).limit(limit).all()

@router.get("/{booking_id}", response_model=schemas.BookingWithDetailsRead)
async def get_booking(booking_id: int, db: Session = Depends(get_db)):
    """Получить бронирование по ID с кэшированием"""
    cache_service = CacheService()
    
    cached_booking = await cache_service.get_cached_booking_details(booking_id)
    if cached_booking:
        return cached_booking
    
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    booking_data = schemas.BookingWithDetailsRead.model_validate(booking)
    
    await cache_service.cache_booking_details(booking_id, booking_data.model_dump())
    
    return booking_data

@router.get("/user/{user_id}/bookings", response_model=List[schemas.BookingWithDetailsRead])
async def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
    """Получить все бронирования пользователя с кэшированием"""
    cache_service = CacheService()
    
    cached_bookings = await cache_service.get_cached_user_bookings(user_id)
    if cached_bookings:
        return cached_bookings
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    bookings = user.bookings
    
    bookings_data = [schemas.BookingWithDetailsRead.model_validate(booking).model_dump() for booking in bookings]
    
    await cache_service.cache_user_bookings(user_id, bookings_data)
    
    return bookings

@router.put("/{booking_id}", response_model=schemas.BookingRead)
async def update_booking(
    booking_id: int,
    booking_update: schemas.BookingUpdate,
    db: Session = Depends(get_db)
):
    """Обновить информацию о бронировании"""
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    if booking.status in [models.BookingStatus.CANCELLED, models.BookingStatus.COMPLETED]:
        raise HTTPException(
            status_code=400,
            detail="Нельзя изменить отмененное или завершенное бронирование"
        )
    
    update_data = booking_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    if 'check_in_date' in update_data or 'check_out_date' in update_data:
        nights = (booking.check_out_date - booking.check_in_date).days
        booking.total_price = nights * booking.room.price_per_night
    
    db.commit()
    db.refresh(booking)

    cache_service = CacheService()
    await cache_service.invalidate_booking_cache(booking_id)
    await cache_service.invalidate_user_cache(booking.user_id)
    
    return booking

@router.put("/{booking_id}/cancel", response_model=schemas.MessageResponse)
async def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    """Отменить бронирование"""
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    if booking.status == models.BookingStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Бронирование уже отменено")
    
    if booking.status == models.BookingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Нельзя отменить завершенное бронирование")
    
    room = booking.room
    room.status = models.RoomStatus.AVAILABLE
    
    booking.status = models.BookingStatus.CANCELLED
    db.commit()
    
    cache_service = CacheService()
    await cache_service.invalidate_booking_cache(booking_id)
    await cache_service.invalidate_user_cache(booking.user_id)
    await cache_service.invalidate_hotel_cache(booking.hotel_id)
    
    return {"message": "Бронирование успешно отменено"}

@router.put("/{booking_id}/check-in", response_model=schemas.MessageResponse)
async def check_in_booking(booking_id: int, db: Session = Depends(get_db)):
    """Зарегистрировать заезд гостя"""
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    if booking.status != models.BookingStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Можно зарегистрировать только подтвержденные бронирования")
    
    booking.status = models.BookingStatus.CHECKED_IN
    db.commit()
    
    cache_service = CacheService()
    await cache_service.invalidate_booking_cache(booking_id)
    
    return {"message": "Заезд успешно зарегистрирован"}

@router.put("/{booking_id}/check-out", response_model=schemas.MessageResponse)
async def check_out_booking(booking_id: int, db: Session = Depends(get_db)):
    """Зарегистрировать выезд гостя"""
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    if booking.status != models.BookingStatus.CHECKED_IN:
        raise HTTPException(status_code=400, detail="Можно зарегистрировать выезд только после заезда")
    
    booking.status = models.BookingStatus.COMPLETED
    
    room = booking.room
    room.status = models.RoomStatus.CLEANING 
    
    db.commit()
    
    cache_service = CacheService()
    await cache_service.invalidate_booking_cache(booking_id)
    await cache_service.invalidate_hotel_cache(booking.hotel_id)
    
    return {"message": "Выезд успешно зарегистрирован"}