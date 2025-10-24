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
            
            rooms = []
            room_types = ["Standard", "Deluxe", "Suite"]
            room_prices = [2500, 4000, 6000]  
            
            for hotel_index, hotel in enumerate(hotels):
                for i in range(5): 
                    room_type = room_types[i % 3]  
                    room = Room(
                        hotel_id=hotel.id,
                        room_number=f"10{i+1}",
                        floor=1 + (i // 3),  
                        room_type=room_type,
                        description=f"{room_type} номер в отеле {hotel.name}",
                        price_per_night=room_prices[i % 3],
                        capacity=2 if room_type == "Standard" else (3 if room_type == "Deluxe" else 4),
                        amenities="WiFi, TV, Кондиционер",
                        status="available"
                    )
                    db.add(room)
                    rooms.append(room)
            db.flush()

            users_data = [
                {"email": "ivan.petrov@example.com", "first_name": "Иван", "last_name": "Петров", "phone": "+79991234567"},
                {"email": "maria.ivanova@example.com", "first_name": "Мария", "last_name": "Иванова", "phone": "+79992345678"},
                {"email": "alex.smirnov@example.com", "first_name": "Алексей", "last_name": "Смирнов", "phone": "+79993456789"}
            ]
            
            users = []
            for user_data in users_data:
                user = User(**user_data)
                db.add(user)
                users.append(user)

            db.flush()

            
            bookings_data = [
                {
                    "user_id": users[0].id,
                    "room_id": rooms[0].id, 
                    "hotel_id": hotels[0].id,
                    "check_in_date": datetime.now() + timedelta(days=7),
                    "check_out_date": datetime.now() + timedelta(days=10),
                    "number_of_guests": 2,
                    "total_price": 7500, 
                    "status": "confirmed",
                    "special_requests": "Прошу номер на высоком этаже"
                },
                {
                    "user_id": users[0].id,
                    "room_id": rooms[3].id, 
                    "hotel_id": hotels[0].id,
                    "check_in_date": datetime.now() + timedelta(days=30),
                    "check_out_date": datetime.now() + timedelta(days=35),
                    "number_of_guests": 3,
                    "total_price": 30000, 
                    "status": "confirmed",
                    "special_requests": "Отмечаем годовщину свадьбы"
                },
                
                {
                    "user_id": users[1].id,
                    "room_id": rooms[5].id, 
                    "hotel_id": hotels[1].id,
                    "check_in_date": datetime.now() + timedelta(days=3),
                    "check_out_date": datetime.now() + timedelta(days=5),
                    "number_of_guests": 1,
                    "total_price": 5000,  
                    "status": "checked_in",
                    "special_requests": "Требуется трансфер из аэропорта"
                },
                {
                    "user_id": users[1].id,
                    "room_id": rooms[8].id,  
                    "hotel_id": hotels[1].id,
                    "check_in_date": datetime.now() - timedelta(days=10),
                    "check_out_date": datetime.now() - timedelta(days=5),
                    "number_of_guests": 2,
                    "total_price": 12000,  
                    "status": "completed",
                    "special_requests": None
                },
                
                
                {
                    "user_id": users[2].id,
                    "room_id": rooms[10].id,  
                    "hotel_id": hotels[2].id,
                    "check_in_date": datetime.now() + timedelta(days=14),
                    "check_out_date": datetime.now() + timedelta(days=21),
                    "number_of_guests": 2,
                    "total_price": 17500,  
                    "status": "confirmed",
                    "special_requests": "Хочу номер с видом на море"
                }
            ]
            
            for booking_data in bookings_data:
                booking = Booking(**booking_data)
                db.add(booking)
                
                if booking.status in ["confirmed", "checked_in"]:
                    room = next((r for r in rooms if r.id == booking.room_id), None)
                    if room:
                        room.status = "occupied"
            
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