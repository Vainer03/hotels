from app.database import SessionLocal, engine
from app.models.hotels import Hotel, Room, User, Booking
from app.database import Base
from datetime import datetime, timedelta
import random

def create_mock_data():
    """Создание моковых данных для тестирования"""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        hotels_data = [
            {
                "name": "Grand Hotel Moscow",
                "description": "Роскошный пятизвездочный отель в самом центре Москвы",
                "address": "ул. Тверская, 1",
                "city": "Москва",
                "country": "Россия",
                "rating": 4.8
            },
            {
                "name": "St. Petersburg Imperial",
                "description": "Элегантный отель с видом на Невский проспект",
                "address": "Невский пр-т, 25",
                "city": "Санкт-Петербург", 
                "country": "Россия",
                "rating": 4.6
            },
            {
                "name": "Sochi Sunrise Resort",
                "description": "Курортный комплекс с собственным пляжем и SPA",
                "address": "ул. Приморская, 45",
                "city": "Сочи",
                "country": "Россия", 
                "rating": 4.4
            },
            {
                "name": "Kazan Palace",
                "description": "Современный отель в историческом центре Казани",
                "address": "ул. Баумана, 15",
                "city": "Казань",
                "country": "Россия",
                "rating": 4.5
            },
            {
                "name": "Novosibirsk Business Hotel",
                "description": "Отель для деловых поездок с конференц-залами",
                "address": "ул. Ленина, 100",
                "city": "Новосибирск",
                "country": "Россия",
                "rating": 4.2
            },
            {
                "name": "Golden Ring Hotel",
                "description": "Уютный отель в историческом городе Золотого кольца",
                "address": "Советская пл., 3",
                "city": "Ярославль", 
                "country": "Россия",
                "rating": 4.3
            }
        ]
        
        hotels = []
        for hotel_data in hotels_data:
            hotel = Hotel(**hotel_data)
            db.add(hotel)
            hotels.append(hotel)
        
        db.flush() 
        print(f"🏨 Создано {len(hotels)} отелей")
        
        room_types = ["Standard", "Deluxe", "Superior", "Family", "Suite", "Business"]
        room_descriptions = {
            "Standard": "Комфортабельный стандартный номер",
            "Deluxe": "Улучшенный номер с дополнительными удобствами", 
            "Superior": "Просторный номер премиум-класса",
            "Family": "Семейный номер с двумя комнатами",
            "Suite": "Люкс с гостиной зоной",
            "Business": "Номер для деловых поездок с рабочим столом"
        }
        
        amenities_options = [
            "WiFi, TV, Кондиционер",
            "WiFi, TV, Кондиционер, Мини-бар",
            "WiFi, TV, Кондиционер, Мини-бар, Сейф",
            "WiFi, TV, Кондиционер, Мини-бар, Сейф, Кофемашина",
            "WiFi, TV, Кондиционер, Мини-бар, Сейф, Кофемашина, Гидромассажная ванна"
        ]
        
        room_statuses = ["available", "available", "available", "maintenance", "cleaning"]
        
        rooms = []
        for hotel in hotels:
            num_rooms = random.randint(10, 15)
            for i in range(num_rooms):
                room_type = random.choice(room_types)
                floor = random.randint(1, 5)
                room_number = f"{floor}{str(i+1).zfill(2)}"
                
                base_price = 2000
                if room_type == "Deluxe":
                    base_price = 3500
                elif room_type == "Superior":
                    base_price = 4500
                elif room_type == "Family":
                    base_price = 5000
                elif room_type == "Suite":
                    base_price = 7000
                elif room_type == "Business":
                    base_price = 4000
                
                if hotel.city == "Москва":
                    base_price *= 1.5
                elif hotel.city == "Санкт-Петербург":
                    base_price *= 1.3
                
                room = Room(
                    hotel_id=hotel.id,
                    room_number=room_number,
                    floor=floor,
                    room_type=room_type,
                    description=room_descriptions[room_type],
                    price_per_night=base_price,
                    capacity=random.randint(1, 4),
                    amenities=random.choice(amenities_options),
                    status=random.choice(room_statuses)
                )
                db.add(room)
                rooms.append(room)
        
        print(f"🛏️ Создано {len(rooms)} комнат")
        
        users_data = [
            {
                "email": "ivan.petrov@example.com",
                "first_name": "Иван",
                "last_name": "Петров",
                "phone": "+79991234567"
            },
            {
                "email": "maria.ivanova@example.com", 
                "first_name": "Мария",
                "last_name": "Иванова",
                "phone": "+79992345678"
            },
            {
                "email": "alex.smirnov@example.com",
                "first_name": "Алексей", 
                "last_name": "Смирнов",
                "phone": "+79993456789"
            },
            {
                "email": "olga.kuznetsova@example.com",
                "first_name": "Ольга",
                "last_name": "Кузнецова", 
                "phone": "+79994567890"
            },
            {
                "email": "dmitry.popov@example.com",
                "first_name": "Дмитрий",
                "last_name": "Попов",
                "phone": "+79995678901"
            },
            {
                "email": "anna.sokolova@example.com",
                "first_name": "Анна",
                "last_name": "Соколова",
                "phone": "+79996789012"
            },
            {
                "email": "sergey.volkov@example.com", 
                "first_name": "Сергей",
                "last_name": "Волков",
                "phone": "+79997890123"
            },
            {
                "email": "elena.romanova@example.com",
                "first_name": "Елена", 
                "last_name": "Романова",
                "phone": "+79998901234"
            },
            {
                "email": "mikhail.fedorov@example.com",
                "first_name": "Михаил",
                "last_name": "Федоров",
                "phone": "+79999012345"
            },
            {
                "email": "natalia.morozova@example.com",
                "first_name": "Наталья",
                "last_name": "Морозова", 
                "phone": "+79990123456"
            }
        ]
        
        users = []
        for user_data in users_data:
            user = User(**user_data)
            db.add(user)
            users.append(user)
        
        db.flush()
        print(f"👥 Создано {len(users)} пользователей")
        
        booking_statuses = ["confirmed", "confirmed", "confirmed", "completed", "cancelled"]
        
        for i in range(20): 
            user = random.choice(users)
            room = random.choice([r for r in rooms if r.status == "available"])
        
            days_from_now = random.randint(1, 60)
            check_in = datetime.now() + timedelta(days=days_from_now)
            check_out = check_in + timedelta(days=random.randint(1, 7))
            
            nights = (check_out - check_in).days
            total_price = room.price_per_night * nights
            
            booking = Booking(
                user_id=user.id,
                hotel_id=room.hotel_id,
                room_id=room.id,
                check_in_date=check_in,
                check_out_date=check_out,
                number_of_guests=random.randint(1, room.capacity),
                total_price=total_price,
                status=random.choice(booking_statuses),
                special_requests=random.choice([
                    None,
                    "Поздний заезд",
                    "Детская кроватка",
                    "Угловой номер",
                    "Вид на море",
                    "Тихый номер"
                ])
            )
            db.add(booking)
        
        print("Создано 20 бронирований")
        
        db.commit()
        print("Моковые данные успешно созданы!")
        
        print("\n Статистика созданных данных:")
        print(f"Отелей: {len(hotels)}")
        print(f"Комнат: {len(rooms)}")
        print(f"Пользователей: {len(users)}")
        print(f"Бронирований: 20")
        
        print("\n🔍 Примеры отелей:")
        for hotel in hotels[:3]:
            hotel_rooms = [r for r in rooms if r.hotel_id == hotel.id]
            available_rooms = [r for r in hotel_rooms if r.status == "available"]
            print(f"  {hotel.name} ({hotel.city}) - {len(available_rooms)}/{len(hotel_rooms)} комнат доступно")
        
        print("\n🔍 Примеры комнат:")
        sample_rooms = random.sample(rooms, 3)
        for room in sample_rooms:
            hotel = next(h for h in hotels if h.id == room.hotel_id)
            print(f"  {hotel.name} - Комната {room.room_number} ({room.room_type}) - {room.price_per_night} руб./ночь")
        
    except Exception as e:
        db.rollback()
        print(f"Ошибка при создании моковых данных: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_mock_data()