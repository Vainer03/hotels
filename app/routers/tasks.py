from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.services.cache_service import CacheService
from app.tasks.email_tasks import send_booking_confirmation_email
from app.tasks.report_tasks import generate_hotel_report
from app.tasks.analytics_tasks import analyze_booking_trends
from app.core.celery import celery_app
import app.schemas.schemas as schemas

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/init-mock-data", response_model=schemas.MessageResponse)
async def init_mock_data():
    """Инициализировать моковые данные (для разработки)"""
    try:
        from app.database import SessionLocal, engine
        from app.models.hotels import Hotel, Room, User, Booking
        from app.database import Base
        from datetime import datetime, timedelta
        import random
        
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        
        try:
            db.query(Booking).delete()
            db.query(Room).delete()
            db.query(Hotel).delete()
            db.query(User).delete()
            
            hotels_data = [
                {
                    "name": "Grand Hotel Moscow",
                    "description": "Роскошный отель в центре Москвы",
                    "address": "ул. Тверская, 1",
                    "city": "Москва",
                    "country": "Россия",
                    "rating": 4.8
                },
                {
                    "name": "St. Petersburg Imperial", 
                    "description": "Элегантный отель в Санкт-Петербурге",
                    "address": "Невский пр-т, 25",
                    "city": "Санкт-Петербург",
                    "country": "Россия", 
                    "rating": 4.6
                },
                {
                    "name": "Sochi Sunrise Resort",
                    "description": "Курортный комплекс в Сочи",
                    "address": "ул. Приморская, 45", 
                    "city": "Сочи",
                    "country": "Россия",
                    "rating": 4.4
                }
            ]
            
            hotels = []
            for hotel_data in hotels_data:
                hotel = Hotel(**hotel_data)
                db.add(hotel)
                hotels.append(hotel)
            
            db.flush()
            
            for hotel in hotels:
                for i in range(5): 
                    room = Room(
                        hotel_id=hotel.id,
                        room_number=f"10{i+1}",
                        floor=1,
                        room_type=random.choice(["Standard", "Deluxe", "Suite"]),
                        description=f"Комфортабельный номер в отеле {hotel.name}",
                        price_per_night=random.randint(2000, 6000),
                        capacity=random.randint(1, 4),
                        amenities="WiFi, TV, Кондиционер",
                        status="available"
                    )
                    db.add(room)
            
            users_data = [
                {"email": "ivan.petrov@example.com", "first_name": "Иван", "last_name": "Петров", "phone": "+79991234567"},
                {"email": "maria.ivanova@example.com", "first_name": "Мария", "last_name": "Иванова", "phone": "+79992345678"},
                {"email": "alex.smirnov@example.com", "first_name": "Алексей", "last_name": "Смирнов", "phone": "+79993456789"}
            ]
            
            for user_data in users_data:
                user = User(**user_data)
                db.add(user)
            
            db.commit()
            
            return {"message": "Моковые данные успешно созданы! Перезагрузите страницу."}
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании моковых данных: {str(e)}")

@router.post("/send-booking-confirmation", response_model=schemas.TaskResponse)
async def send_booking_confirmation_task(
    task_data: schemas.EmailTaskData,
    background_tasks: BackgroundTasks
):
    """Запустить задачу отправки подтверждения бронирования"""
    try:
        task = send_booking_confirmation_email.delay(
            to_email=task_data.to_email,
            user_name=task_data.user_name,
            booking_data=task_data.booking_data
        )
        
        return {
            "task_id": task.id,
            "status": "queued",
            "message": "Email task queued successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue email task: {str(e)}")

@router.post("/generate-report", response_model=schemas.TaskResponse)
async def generate_hotel_report_task(
    report_data: schemas.ReportTaskData,
    background_tasks: BackgroundTasks
):
    """Запустить задачу генерации отчета"""
    try:
        task = generate_hotel_report.delay(
            hotel_id=report_data.hotel_id,
            start_date=report_data.start_date.isoformat(),
            end_date=report_data.end_date.isoformat(),
            report_type=report_data.report_type
        )
        
        return {
            "task_id": task.id,
            "status": "queued", 
            "message": "Report generation task queued successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue report task: {str(e)}")

@router.post("/analyze-bookings", response_model=schemas.TaskResponse)
async def analyze_bookings_task(
    analytics_data: schemas.AnalyticsTaskData,
    background_tasks: BackgroundTasks
):
    """Запустить задачу аналитики бронирований"""
    try:
        task = analyze_booking_trends.delay(
            hotel_id=analytics_data.hotel_id,
            period=analytics_data.period
        )
        
        return {
            "task_id": task.id,
            "status": "queued",
            "message": "Analytics task queued successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue analytics task: {str(e)}")

@router.get("/status/{task_id}", response_model=schemas.TaskStatusResponse)
async def get_task_status(task_id: str):
    """Получить статус задачи Celery"""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        response_data = {
            "task_id": task_id,
            "status": task_result.status,
            "result": None
        }
        
        if task_result.ready():
            if task_result.successful():
                response_data["result"] = task_result.result
            else:
                response_data["error"] = str(task_result.result)
        
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@router.get("/cache/stats", response_model=Dict[str, Any])
async def get_cache_stats():
    """Получить статистику кэша"""
    try:
        cache_service = CacheService()
        stats = await cache_service.get_booking_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.post("/cache/clear", response_model=schemas.MessageResponse)
async def clear_cache(pattern: str = "*"):
    """Очистить кэш по шаблону"""
    try:
        cache_service = CacheService()
        manager = await cache_service._get_manager()
        
        keys = await manager.keys(pattern)
        for key in keys:
            await manager.delete_key(key)
        
        return {"message": f"Cache cleared for pattern: {pattern}, deleted {len(keys)} keys"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")