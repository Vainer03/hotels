# tests/test_hotels.py
import pytest
from datetime import datetime

class TestHotels:
    def test_create_hotel_success(self, client, sample_hotel_data):
        response = client.post("/api/v1/hotels/", json=sample_hotel_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_hotel_data["name"]
        assert data["city"] == sample_hotel_data["city"]
        assert "id" in data
        assert "created_at" in data

    def test_create_hotel_missing_required_fields(self, client):
        incomplete_data = {
            "name": "Test Hotel"
            # missing required fields
        }
        response = client.post("/api/v1/hotels/", json=incomplete_data)
        assert response.status_code == 422  # Validation error

    def test_get_hotel_by_id_success(self, client, sample_hotel_data):
        # Сначала создаем отель
        create_response = client.post("/api/v1/hotels/", json=sample_hotel_data)
        hotel_id = create_response.json()["id"]
        
        # Получаем отель по ID
        response = client.get(f"/api/v1/hotels/{hotel_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == hotel_id
        assert data["name"] == sample_hotel_data["name"]

    def test_get_hotel_not_found(self, client):
        response = client.get("/api/v1/hotels/9999")
        assert response.status_code == 404
        assert "Отель не найден" in response.json()["detail"]

    def test_get_hotels_with_filters(self, client, sample_hotel_data):
        # Создаем несколько отелей
        client.post("/api/v1/hotels/", json=sample_hotel_data)
        
        hotel2_data = sample_hotel_data.copy()
        hotel2_data.update({
            "name": "Beach Resort",
            "city": "Sochi",
            "country": "Russia"
        })
        client.post("/api/v1/hotels/", json=hotel2_data)
        
        # Фильтр по городу
        response = client.get("/api/v1/hotels/?city=Sochi")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["city"] == "Sochi"
        
        # Фильтр по стране
        response = client.get("/api/v1/hotels/?country=Russia")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Пагинация
        response = client.get("/api/v1/hotels/?skip=1&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_update_hotel_success(self, client, sample_hotel_data):
        # Создаем отель
        create_response = client.post("/api/v1/hotels/", json=sample_hotel_data)
        hotel_id = create_response.json()["id"]
        
        # Обновляем отель
        update_data = {
            "name": "Updated Hotel Name",
            "rating": 5.0
        }
        response = client.put(f"/api/v1/hotels/{hotel_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Hotel Name"
        assert data["rating"] == 5.0
        assert data["city"] == sample_hotel_data["city"]  # Неизмененные поля

    def test_update_hotel_not_found(self, client):
        update_data = {"name": "Updated Name"}
        response = client.put("/api/v1/hotels/9999", json=update_data)
        assert response.status_code == 404

    def test_delete_hotel_success(self, client, sample_hotel_data):
        # Создаем отель
        create_response = client.post("/api/v1/hotels/", json=sample_hotel_data)
        hotel_id = create_response.json()["id"]
        
        # Удаляем отель
        response = client.delete(f"/api/v1/hotels/{hotel_id}")
        assert response.status_code == 200
        assert "успешно удален" in response.json()["message"]
        
        # Проверяем, что отель удален
        response = client.get(f"/api/v1/hotels/{hotel_id}")
        assert response.status_code == 404

    def test_delete_hotel_with_rooms(self, client, sample_hotel_data, sample_room_data):
        # Создаем отель
        hotel_response = client.post("/api/v1/hotels/", json=sample_hotel_data)
        hotel_id = hotel_response.json()["id"]
        
        # Создаем комнату в отеле
        room_data = sample_room_data.copy()
        room_data["hotel_id"] = hotel_id
        client.post("/api/v1/rooms/", json=room_data)
        
        # Пытаемся удалить отель с комнатами
        response = client.delete(f"/api/v1/hotels/{hotel_id}")
        assert response.status_code == 400
        assert "Нельзя удалить отель с существующими комнатами" in response.json()["detail"]