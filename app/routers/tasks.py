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
from app.core.enums import UserRole
from app.core.security import get_password_hash 

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/init-mock-data", response_model=schemas.MessageResponse)
async def init_mock_data():
    """Инициализировать моковые данные (для разработки)"""
    try:
        from app.database import SessionLocal, engine
        from app.models.hotels import Hotel, Room, User, Booking
        from app.database import Base
        from datetime import datetime, timedelta
        from app.core.security import get_password_hash 
        
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
                    "description": "Роскошный отель в центре Москвы с видом на Кремль",
                    "address": "ул. Тверская, 1",
                    "city": "Москва",
                    "country": "Россия",
                    "rating": 4.8
                },
                {
                    "name": "St. Petersburg Imperial", 
                    "description": "Элегантный отель в историческом центре Санкт-Петербурга",
                    "address": "Невский пр-т, 25",
                    "city": "Санкт-Петербург",
                    "country": "Россия", 
                    "rating": 4.6
                },
                {
                    "name": "Sochi Sunrise Resort",
                    "description": "Курортный комплекс в Сочи с собственным пляжем",
                    "address": "ул. Приморская, 45", 
                    "city": "Сочи",
                    "country": "Россия",
                    "rating": 4.4
                },
                {
                    "name": "Kazan Palace",
                    "description": "Современный отель в центре Казани рядом с Кремлем",
                    "address": "ул. Баумана, 15",
                    "city": "Казань",
                    "country": "Россия",
                    "rating": 4.5
                },
                {
                    "name": "Golden Ring Hotel",
                    "description": "Уютный отель в историческом центре Ярославля",
                    "address": "ул. Кирова, 8",
                    "city": "Ярославль",
                    "country": "Россия",
                    "rating": 4.3
                },
                {
                    "name": "Ural Mountains Resort",
                    "description": "Горнолыжный курорт в предгорьях Урала",
                    "address": "ул. Горная, 12",
                    "city": "Екатеринбург",
                    "country": "Россия",
                    "rating": 4.2
                },
                {
                    "name": "Volga River View",
                    "description": "Отель с панорамным видом на Волгу в Нижнем Новгороде",
                    "address": "наб. Верхне-Волжская, 10",
                    "city": "Нижний Новгород",
                    "country": "Россия",
                    "rating": 4.4
                },
                {
                    "name": "Siberian Taiga Lodge",
                    "description": "Эко-отель в сибирской тайге с банным комплексом",
                    "address": "ул. Лесная, 5",
                    "city": "Новосибирск",
                    "country": "Россия",
                    "rating": 4.1
                }
            ]
            
            hotels = []
            for hotel_data in hotels_data:
                hotel = Hotel(**hotel_data)
                db.add(hotel)
                hotels.append(hotel)
            
            db.flush()
            
            rooms = []
            room_types = ["Standard", "Deluxe", "Suite", "Family", "Business", "Presidential"]
            room_prices = [2500, 4000, 6000, 5000, 7000, 12000]
            capacities = [2, 3, 4, 5, 2, 6]
            
            for hotel_index, hotel in enumerate(hotels):
                for floor in range(1, 6): 
                    for room_num in range(1, 11):  
                        room_index = (floor + room_num) % len(room_types)
                        room_type = room_types[room_index]
                        
                        room = Room(
                            hotel_id=hotel.id,
                            room_number=f"{floor}{room_num:02d}",
                            floor=floor,
                            room_type=room_type,
                            description=f"{room_type} номер в отеле {hotel.name}. {get_room_description(room_type, hotel.city)}",
                            price_per_night=room_prices[room_index],
                            capacity=capacities[room_index],
                            amenities=get_room_amenities(room_type),
                            status="available"
                        )
                        db.add(room)
                        rooms.append(room)
            
            db.flush()

            users_data = [
                {
                    "email": "admin@hotels.com", 
                    "first_name": "Алексей", 
                    "last_name": "Администраторов", 
                    "phone": "+79990000001",
                    "role": UserRole.ADMIN,
                    "password": "admin123" 
                },
                {
                    "email": "manager@hotels.com", 
                    "first_name": "Мария", 
                    "last_name": "Менеджерова", 
                    "phone": "+79990000002",
                    "role": UserRole.ADMIN,
                    "password": "manager123"  
                },
                {
                    "email": "ivan.petrov@example.com", 
                    "first_name": "Иван", 
                    "last_name": "Петров", 
                    "phone": "+79991234567",
                    "role": UserRole.USER,
                    "password": "password123" 
                },
                {
                    "email": "maria.ivanova@example.com", 
                    "first_name": "Мария", 
                    "last_name": "Иванова", 
                    "phone": "+79992345678",
                    "role": UserRole.USER,
                    "password": "password123"
                },
                {
                    "email": "alex.smirnov@example.com", 
                    "first_name": "Алексей", 
                    "last_name": "Смирнов", 
                    "phone": "+79993456789",
                    "role": UserRole.USER,
                    "password": "password123"
                },
                {
                    "email": "olga.sidorova@example.com", 
                    "first_name": "Ольга", 
                    "last_name": "Сидорова", 
                    "phone": "+79994567890",
                    "role": UserRole.USER,
                    "password": "password123"
                },
                {
                    "email": "dmitry.kuznetsov@example.com", 
                    "first_name": "Дмитрий", 
                    "last_name": "Кузнецов", 
                    "phone": "+79995678901",
                    "role": UserRole.USER,
                    "password": "password123"
                },
                {
                    "email": "ekaterina.popova@example.com", 
                    "first_name": "Екатерина", 
                    "last_name": "Попова", 
                    "phone": "+79996789012",
                    "role": UserRole.USER,
                    "password": "password123"
                },
                {
                    "email": "sergey.volkov@example.com", 
                    "first_name": "Сергей", 
                    "last_name": "Волков", 
                    "phone": "+79997890123",
                    "role": UserRole.USER,
                    "password": "password123"
                },
                {
                    "email": "natalia.fedorova@example.com", 
                    "first_name": "Наталия", 
                    "last_name": "Федорова", 
                    "phone": "+79998901234",
                    "role": UserRole.USER,
                    "password": "password123"
                },
                {
                    "email": "andrey.morozov@example.com", 
                    "first_name": "Андрей", 
                    "last_name": "Морозов", 
                    "phone": "+79999012345",
                    "role": UserRole.USER,
                    "password": "password123"
                },
                {
                    "email": "tatyana.nikitina@example.com", 
                    "first_name": "Татьяна", 
                    "last_name": "Никитина", 
                    "phone": "+79990123456",
                    "role": UserRole.USER,
                    "password": "password123"
                },
                {
                    "email": "business.traveler@example.com", 
                    "first_name": "Артем", 
                    "last_name": "Деловой", 
                    "phone": "+79991112233",
                    "role": UserRole.USER,
                    "password": "password123"
                },
                {
                    "email": "family.vacation@example.com", 
                    "first_name": "Светлана", 
                    "last_name": "Семейная", 
                    "phone": "+79992223344",
                    "role": UserRole.USER,
                    "password": "password123"
                }
            ]
            
            users = []
            for user_data in users_data:
                password = user_data.pop('password')
                hashed_password = get_password_hash(password)
                
                user = User(
                    email=user_data["email"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    phone=user_data["phone"],
                    role=user_data["role"],
                    hashed_password=hashed_password 
                )
                db.add(user)
                users.append(user)

            db.flush()

            bookings_data = [
                {
                    "user_id": users[2].id, 
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
                    "user_id": users[2].id, 
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
                    "user_id": users[3].id, 
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
                    "user_id": users[4].id,
                    "room_id": rooms[10].id,  
                    "hotel_id": hotels[2].id,
                    "check_in_date": datetime.now() + timedelta(days=14),
                    "check_out_date": datetime.now() + timedelta(days=21),
                    "number_of_guests": 2,
                    "total_price": 17500,  
                    "status": "confirmed",
                    "special_requests": "Хочу номер с видом на море"
                },
                {
                    "user_id": users[3].id, 
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
                    "user_id": users[5].id, 
                    "room_id": rooms[15].id,
                    "hotel_id": hotels[3].id,
                    "check_in_date": datetime.now() - timedelta(days=20),
                    "check_out_date": datetime.now() - timedelta(days=15),
                    "number_of_guests": 4,
                    "total_price": 20000,
                    "status": "completed",
                    "special_requests": "С детской кроваткой"
                },
                {
                    "user_id": users[6].id, 
                    "room_id": rooms[20].id,
                    "hotel_id": hotels[4].id,
                    "check_in_date": datetime.now() + timedelta(days=5),
                    "check_out_date": datetime.now() + timedelta(days=8),
                    "number_of_guests": 2,
                    "total_price": 9000,
                    "status": "cancelled",
                    "special_requests": None
                },
                {
                    "user_id": users[0].id,  
                    "room_id": rooms[25].id,
                    "hotel_id": hotels[5].id,
                    "check_in_date": datetime.now() + timedelta(days=12),
                    "check_out_date": datetime.now() + timedelta(days=15),
                    "number_of_guests": 3,
                    "total_price": 13500,
                    "status": "confirmed",
                    "special_requests": "Служебная командировка"
                },
                {
                    "user_id": users[1].id, 
                    "room_id": rooms[30].id,
                    "hotel_id": hotels[6].id,
                    "check_in_date": datetime.now() + timedelta(days=25),
                    "check_out_date": datetime.now() + timedelta(days=28),
                    "number_of_guests": 2,
                    "total_price": 12000,
                    "status": "confirmed",
                    "special_requests": "Проверка качества обслуживания"
                },
                {
                    "user_id": users[7].id, 
                    "room_id": rooms[35].id,
                    "hotel_id": hotels[7].id,
                    "check_in_date": datetime.now() + timedelta(days=40),
                    "check_out_date": datetime.now() + timedelta(days=45),
                    "number_of_guests": 6,
                    "total_price": 60000,
                    "status": "confirmed",
                    "special_requests": "Семейный отдых с детьми"
                },
                {
                    "user_id": users[8].id, 
                    "room_id": rooms[40].id,
                    "hotel_id": hotels[0].id,
                    "check_in_date": datetime.now() + timedelta(days=18),
                    "check_out_date": datetime.now() + timedelta(days=22),
                    "number_of_guests": 2,
                    "total_price": 16000,
                    "status": "confirmed",
                    "special_requests": "Романтический уикенд"
                },
                {
                    "user_id": users[9].id, 
                    "room_id": rooms[45].id,
                    "hotel_id": hotels[1].id,
                    "check_in_date": datetime.now() + timedelta(days=8),
                    "check_out_date": datetime.now() + timedelta(days=11),
                    "number_of_guests": 1,
                    "total_price": 12000,
                    "status": "confirmed",
                    "special_requests": "Командировка"
                },
                {
                    "user_id": users[10].id,  
                    "room_id": rooms[50].id,
                    "hotel_id": hotels[2].id,
                    "check_in_date": datetime.now() + timedelta(days=35),
                    "check_out_date": datetime.now() + timedelta(days=42),
                    "number_of_guests": 4,
                    "total_price": 28000,
                    "status": "confirmed",
                    "special_requests": "Отдых с семьей"
                },
                {
                    "user_id": users[11].id, 
                    "room_id": rooms[55].id,
                    "hotel_id": hotels[3].id,
                    "check_in_date": datetime.now() + timedelta(days=22),
                    "check_out_date": datetime.now() + timedelta(days=25),
                    "number_of_guests": 2,
                    "total_price": 15000,
                    "status": "confirmed",
                    "special_requests": "Экскурсия по городу"
                },
                {
                    "user_id": users[12].id, 
                    "room_id": rooms[60].id,
                    "hotel_id": hotels[4].id,
                    "check_in_date": datetime.now() + timedelta(days=2),
                    "check_out_date": datetime.now() + timedelta(days=4),
                    "number_of_guests": 1,
                    "total_price": 14000,
                    "status": "confirmed",
                    "special_requests": "Бизнес-поездка, нужен хороший Wi-Fi"
                },
                {
                    "user_id": users[13].id, 
                    "room_id": rooms[65].id,
                    "hotel_id": hotels[5].id,
                    "check_in_date": datetime.now() + timedelta(days=50),
                    "check_out_date": datetime.now() + timedelta(days=60),
                    "number_of_guests": 5,
                    "total_price": 45000,
                    "status": "confirmed",
                    "special_requests": "Семейный отпуск, нужны детские кровати"
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
            
            admin_count = len([u for u in users if u.role == UserRole.ADMIN])
            user_count = len([u for u in users if u.role == UserRole.USER])
            
            return {
                "message": f"Моковые данные успешно созданы! Создано: {len(hotels)} отелей, {len(rooms)} комнат, {len(users)} пользователей ({admin_count} администраторов, {user_count} пользователей), {len(bookings_data)} бронирований. Перезагрузите страницу."
            }
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании моковых данных: {str(e)}")

def get_room_description(room_type: str, city: str) -> str:
    """Генерирует описание комнаты в зависимости от типа и города"""
    descriptions = {
        "Standard": f"Комфортабельный стандартный номер в {city}",
        "Deluxe": f"Просторный улучшенный номер в {city} с дополнительными удобствами",
        "Suite": f"Роскошный люкс в {city} с гостиной зоной",
        "Family": f"Семейный номер в {city} идеально подходящий для отдыха с детьми",
        "Business": f"Бизнес-номер в {city} с рабочим столом и улучшенным Wi-Fi",
        "Presidential": f"Президентский люкс в {city} с панорамным видом"
    }
    return descriptions.get(room_type, f"Комфортабельный номер в {city}")

def get_room_amenities(room_type: str) -> str:
    """Возвращает список удобств в зависимости от типа комнаты"""
    base_amenities = "WiFi, TV, Кондиционер, Сейф"
    
    amenities_by_type = {
        "Standard": f"{base_amenities}, Фен, Чайник",
        "Deluxe": f"{base_amenities}, Мини-бар, Халаты, Тапочки",
        "Suite": f"{base_amenities}, Гостиная зона, Мини-кухня, Джакузи",
        "Family": f"{base_amenities}, Детская кроватка, Игровая зона",
        "Business": f"{base_amenities}, Рабочий стол, Принтер, Кофемашина",
        "Presidential": f"{base_amenities}, Отдельная гостиная, Столовая, Личный дворецкий"
    }
    
    return amenities_by_type.get(room_type, base_amenities)

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