from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.hotels import User
from app.core.enums import UserRole

async def get_current_user(
        user_id: int,
        db: Session = Depends(get_db)
) -> User:
    """Получить текущего пользователя по ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user

async def require_admin(current_user: User = Depends(get_current_user)):
    """Требовать права администратора"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    return current_user

async def require_user_or_admin(current_user: User = Depends(get_current_user)):
    """Требовать права пользователя или администратора"""
    if current_user.role not in [UserRole.USER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется авторизация"
        )
    return current_user

async def require_user(current_user: User = Depends(get_current_user)):
    """Требовать права обычного пользователя"""
    if current_user.role != UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права пользователя"
        )
    return current_user
