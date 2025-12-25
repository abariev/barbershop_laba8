import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import asyncio
import database as db
from app import app

# Тестовый клиент
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Настройка тестовой БД"""
    # Используем тестовую БД
    import database
    database.DB_PATH = "test_lab.db"

    # Инициализируем БД
    asyncio.run(db.init_db())
    yield

    # Очистка после тестов (можно удалить файл тестовой БД)
    import os
    if os.path.exists("test_lab.db"):
        os.remove("test_lab.db")


def test_create_appointment():
    """Тест создания заявки"""
    appointment_data = {
        "client_name": "Иван Петров",
        "service_type": "Стрижка",
        "appointment_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "notes": "Тестовая заявка"
    }

    response = client.post("/api/appointments", json=appointment_data)

    assert response.status_code == 200
    data = response.json()
    assert data["client_name"] == "Иван Петров"
    assert data["service_type"] == "Стрижка"
    assert "id" in data

    # Сохраняем ID для следующих тестов
    return data["id"]


def test_get_appointments():
    """Тест получения списка заявок"""
    response = client.get("/api/appointments")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_reschedule_appointment():
    """Тест переноса заявки"""
    # Сначала создаем заявку
    appointment_data = {
        "client_name": "Мария Сидорова",
        "service_type": "Окрашивание",
        "appointment_date": (datetime.now() + timedelta(days=2)).isoformat(),
    }

    create_response = client.post("/api/appointments", json=appointment_data)
    appointment_id = create_response.json()["id"]

    # Переносим на новую дату
    new_date = (datetime.now() + timedelta(days=3)).isoformat()

    response = client.patch(
        f"/api/appointments/{appointment_id}/reschedule",
        params={"new_date": new_date}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == appointment_id

    # Проверяем, что дата изменилась
    assert data["appointment_date"].startswith(
        (datetime.now() + timedelta(days=3)).date().isoformat()
    )


def test_health_check():
    """Тест проверки здоровья"""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data