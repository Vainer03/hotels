from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import os

Base = declarative_base()

def get_database_url():
    """
    Получить URL базы данных в зависимости от окружения.
    Используется SQLite для разработки.
    """

    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        return database_url
    else:
        return "sqlite:///./hotel_booking.db"

database_url = get_database_url()

if database_url.startswith("sqlite"):
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False 
    )
else:
    engine = create_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency для получения сессии базы данных.
    Используется в Depends() FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Создать все таблицы в базе данных.
    Вызывается при старте приложения.
    """
    Base.metadata.create_all(bind=engine)