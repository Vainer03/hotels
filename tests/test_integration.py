# tests/test_integration.py
import pytest
from datetime import datetime, timedelta

class TestIntegration:
    def test_complete_booking_flow(self, client, sample_hotel_data, sample_room_data, sample_user_data):
        """Полный тест потока бронирования"""
        
        # 1. Создаем отель
        hotel_response = client.post("/api/v1/hotels/", json=sample_hotel_data)
        hotel_id = hotel_response.json()["id"]
        
        # 2. Создаем комнату
        room_data = sample_room_data.copy()
        room_data["hotel_id"] = hotel_id
        room_response = client.post("/api/v1/rooms/", json=room_data)
        room_id = room_response.json()["id"]
        
        # 3. Создаем пользователя
        user_response = client.post("/api/v1/users/", json=sample_user_data)
        user_id = user_response.json()["id"]
        
        # 4. Ищем доступные комнаты
        check_in = (datetime.now() + timedelta(days=1)).isoformat()
        check_out = (datetime.now() + timedelta(days=3)).isoformat()
        
        search_response = client.get(
            f"/api/v1/rooms/search/available?city={sample_hotel_data['city']}&check_in={check_in}&check_out={check_out}"
        )
        assert len(search_response.json()) == 1
        
        # 5. Создаем бронирование
        booking_data = {
            "user_id": user_id,
            "hotel_id": hotel_id,
            "room_id": room_id,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "number_of_guests": 2
        }
        booking_response = client.post("/api/v1/bookings/", json=booking_data)
        assert booking_response.status_code == 200
        booking_id = booking_response.json()["id"]
        
        # 6. Проверяем, что комната стала занятой
        room_check_response = client.get(f"/api/v1/rooms/{room_id}")
        assert room_check_response.json()["status"] == "occupied"
        
        # 7. Проверяем, что комната больше не доступна для поиска
        search_response2 = client.get(
            f"/api/v1/rooms/search/available?city={sample_hotel_data['city']}&check_in={check_in}&check_out={check_out}"
        )
        assert len(search_response2.json()) == 0
        
        # 8. Отменяем бронирование
        cancel_response = client.put(f"/api/v1/bookings/{booking_id}/cancel")
        assert cancel_response.status_code == 200
        
        # 9. Проверяем, что комната снова доступна
        room_check_response2 = client.get(f"/api/v1/rooms/{room_id}")
        assert room_check_response2.json()["status"] == "available"