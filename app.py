from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
from contextlib import asynccontextmanager
import database as db
from typing import Optional


# Pydantic модели для валидации
class AppointmentCreate(BaseModel):
    client_name: str
    service_type: str
    appointment_date: datetime
    notes: Optional[str] = ""


class AppointmentUpdate(BaseModel):
    client_name: Optional[str] = None
    service_type: Optional[str] = None
    appointment_date: Optional[datetime] = None
    notes: Optional[str] = None


# Жизненный цикл приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    # При запуске: инициализируем БД
    await db.init_db()
    print("🚀 Приложение запущено")
    yield
    # При остановке
    print("🛑 Приложение останавливается")


# Создаем приложение FastAPI
app = FastAPI(
    title="Barbershop Admin API",
    description="Админ-панель для управления заявками парикмахерской",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 1. Главная страница (фронтенд)
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content


# 2. Получить все заявки
@app.get("/api/appointments")
async def get_appointments():
    """Получить список всех заявок"""
    appointments = await db.get_all_appointments()
    return appointments


# 3. Создать заявку
@app.post("/api/appointments")
async def create_appointment(appointment: AppointmentCreate):
    """Создать новую заявку"""
    try:
        result = await db.create_appointment(
            client_name=appointment.client_name,
            service_type=appointment.service_type,
            appointment_date=appointment.appointment_date.isoformat(),
            notes=appointment.notes
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 4. Получить заявку по ID
@app.get("/api/appointments/{appointment_id}")
async def get_appointment(appointment_id: int):
    """Получить заявку по ID"""
    appointment = await db.get_appointment_by_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return appointment


# 5. Обновить заявку
@app.put("/api/appointments/{appointment_id}")
async def update_appointment(
        appointment_id: int,
        appointment: AppointmentUpdate
):
    """Обновить заявку"""
    update_data = {}

    if appointment.client_name is not None:
        update_data['client_name'] = appointment.client_name

    if appointment.service_type is not None:
        update_data['service_type'] = appointment.service_type

    if appointment.appointment_date is not None:
        update_data['appointment_date'] = appointment.appointment_date.isoformat()

    if appointment.notes is not None:
        update_data['notes'] = appointment.notes

    result = await db.update_appointment(appointment_id, **update_data)

    if not result:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    return result


# 6. Удалить заявку
@app.delete("/api/appointments/{appointment_id}")
async def delete_appointment(appointment_id: int):
    """Удалить заявку"""
    success = await db.delete_appointment(appointment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return {"message": "Заявка успешно удалена"}


# 7. Перенести заявку
@app.patch("/api/appointments/{appointment_id}/reschedule")
async def reschedule_appointment(
        appointment_id: int,
        new_date: datetime
):
    """Перенести заявку на другую дату"""
    result = await db.reschedule_appointment(
        appointment_id,
        new_date.isoformat()
    )

    if not result:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    return result


# 8. Проверка здоровья
@app.get("/api/health")
async def health_check():
    """Проверка состояния API"""
    try:
        appointments = await db.get_all_appointments()
        return {
            "status": "healthy",
            "database": "connected",
            "appointments_count": len(appointments),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Запуск сервера
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )