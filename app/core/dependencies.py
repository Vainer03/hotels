from fastapi import Depends, HTTPException, status, Query, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.hotels import User
from app.core.enums import UserRole
from app.core.security import verify_token

security = HTTPBearer()

async def get_current_user_path(
    user_id: int = Path(..., description="ID пользователя"),
    db: Session = Depends(get_db)
) -> User:
    """Получить текущего пользователя по ID из path параметра"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user

async def get_current_user_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Получить текущего пользователя из JWT токена"""
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    
    if email is None or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
        )
    
    user = db.query(User).filter(User.email == email, User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    
    return user

async def require_admin_path(current_user: User = Depends(get_current_user_path)):
    """Требовать права администратора (старый подход)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    return current_user

async def require_user_or_admin_path(current_user: User = Depends(get_current_user_path)):
    """Требовать права пользователя или администратора (старый подход)"""
    if current_user.role not in [UserRole.USER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется авторизация"
        )
    return current_user

async def require_user_path(current_user: User = Depends(get_current_user_path)):
    """Требовать права обычного пользователя (старый подход)"""
    if current_user.role != UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права пользователя"
        )
    return current_user

async def require_admin_jwt(current_user: User = Depends(get_current_user_jwt)):
    """Требовать права администратора (новый подход)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    return current_user

async def require_user_or_admin_jwt(current_user: User = Depends(get_current_user_jwt)):
    """Требовать права пользователя или администратора (новый подход)"""
    if current_user.role not in [UserRole.USER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется авторизация"
        )
    return current_user

async def require_user_jwt(current_user: User = Depends(get_current_user_jwt)):
    """Требовать права обычного пользователя (новый подход)"""
    if current_user.role != UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права пользователя"
        )
    return current_user

get_current_user = get_current_user_path
require_admin = require_admin_path
require_user_or_admin = require_user_or_admin_path
require_user = require_user_path