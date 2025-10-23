# tests/test_users.py
import pytest

class TestUsers:
    def test_create_user_success(self, client, sample_user_data):
        response = client.post("/api/v1/users/", json=sample_user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["first_name"] == sample_user_data["first_name"]
        assert "id" in data
        assert "created_at" in data

    def test_create_user_duplicate_email(self, client, sample_user_data):
        # Первый пользователь
        client.post("/api/v1/users/", json=sample_user_data)
        
        # Второй пользователь с тем же email
        response = client.post("/api/v1/users/", json=sample_user_data)
        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]

    def test_get_user_by_id(self, client, sample_user_data):
        create_response = client.post("/api/v1/users/", json=sample_user_data)
        user_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == sample_user_data["email"]

    def test_update_user_success(self, client, sample_user_data):
        create_response = client.post("/api/v1/users/", json=sample_user_data)
        user_id = create_response.json()["id"]
        
        update_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+0987654321"
        }
        response = client.put(f"/api/v1/users/{user_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"
        assert data["phone"] == "+0987654321"
        assert data["email"] == sample_user_data["email"]  # Email не менялся

    def test_update_user_duplicate_email(self, client, sample_user_data):
        # Создаем первого пользователя
        user1_response = client.post("/api/v1/users/", json=sample_user_data)
        user1_id = user1_response.json()["id"]
        
        # Создаем второго пользователя
        user2_data = sample_user_data.copy()
        user2_data["email"] = "user2@example.com"
        user2_response = client.post("/api/v1/users/", json=user2_data)
        user2_id = user2_response.json()["id"]
        
        # Пытаемся обновить второго пользователя с email первого
        update_data = {"email": sample_user_data["email"]}
        response = client.put(f"/api/v1/users/{user2_id}", json=update_data)
        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]

    def test_delete_user_success(self, client, sample_user_data):
        create_response = client.post("/api/v1/users/", json=sample_user_data)
        user_id = create_response.json()["id"]
        
        response = client.delete(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        assert "успешно удален" in response.json()["message"]
        
        # Проверяем, что пользователь удален
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 404