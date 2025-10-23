from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import app.models.hotels as models
import app.schemas.schemas as schemas
from app.database import get_db
from app.services.cache_service import CacheService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.UserRead)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Создать нового пользователя"""
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким email уже существует"
        )
    
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[schemas.UserRead])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список всех пользователей"""
    return db.query(models.User).offset(skip).limit(limit).all()

@router.get("/{user_id}", response_model=schemas.UserRead)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Получить пользователя по ID"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.put("/{user_id}", response_model=schemas.UserRead)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db)
):
    """Обновить информацию о пользователе"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user_update.email and user_update.email != user.email:
        existing_user = db.query(models.User).filter(models.User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Пользователь с таким email уже существует"
            )
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    cache_service = CacheService()
    await cache_service.invalidate_user_cache(user_id)
    
    return user

@router.delete("/{user_id}", response_model=schemas.MessageResponse)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Удалить пользователя"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    active_bookings = db.query(models.Booking).filter(
        models.Booking.user_id == user_id,
        models.Booking.status.in_([models.BookingStatus.CONFIRMED, models.BookingStatus.CHECKED_IN])
    ).count()
    
    if active_bookings > 0:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить пользователя с активными бронированиями"
        )
    
    db.delete(user)
    db.commit()
    
    cache_service = CacheService()
    await cache_service.invalidate_user_cache(user_id)
    
    return {"message": "Пользователь успешно удален"}