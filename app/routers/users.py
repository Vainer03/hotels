from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import app.models.hotels as models
import app.schemas.schemas as schemas
from app.database import get_db
from app.services.cache_service import CacheService
from app.core.dependencies import get_current_user, require_admin, require_user, require_user_or_admin
from app.core.enums import UserRole

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.UserRead)
async def create_user(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)):
    """Создать нового пользователя"""
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким email уже существует"
        )
    if current_user.role != UserRole.ADMIN and user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав для создания администратора"
        )
    
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/register", response_model=schemas.UserRead)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя (публичный эндпоинт)"""
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким email уже существует"
        )
    
    user_data = user.model_dump()
    user_data['role'] = UserRole.USER
    
    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[schemas.UserRead])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Получить список всех пользователей"""
    return db.query(models.User).offset(skip).limit(limit).all()

@router.get("/me", response_model=schemas.UserRead)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """Получить информацию о текущем пользователе"""
    return current_user

@router.get("/{user_id}", response_model=schemas.UserRead)
async def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_or_admin)
):
    """Получить пользователя по ID"""
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав для просмотра информации этого пользователя"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.put("/{user_id}", response_model=schemas.UserRead)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_or_admin)
):
    """Обновить информацию о пользователе"""
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав для обновления информации этого пользователя"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if current_user.role != UserRole.ADMIN and user_update.role:
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав для изменения роли"
        )
    
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
async def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)  # Только админ может удалять пользователей
):
    """Удалить пользователя (только для администраторов)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    db.delete(user)
    db.commit()
    
    cache_service = CacheService()
    await cache_service.invalidate_user_cache(user_id)
    
    return {"message": "Пользователь успешно удален"}