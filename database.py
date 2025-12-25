import aiosqlite
import asyncio
from datetime import datetime

DB_PATH = "lab.db"


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Включаем поддержку внешних ключей
        await db.execute("PRAGMA foreign_keys = ON")

        # Создаем таблицу заявок
        await db.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                service_type TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Создаем индекс для быстрого поиска по дате
        await db.execute('''
            CREATE INDEX IF NOT EXISTS idx_appointment_date 
            ON appointments(appointment_date)
        ''')

        await db.commit()
        print(f"✅ База данных инициализирована: {DB_PATH}")


async def get_all_appointments():
    """Получить все заявки"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT * FROM appointments 
            ORDER BY appointment_date ASC
        ''')
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_appointment_by_id(appointment_id: int):
    """Получить заявку по ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'SELECT * FROM appointments WHERE id = ?',
            (appointment_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_appointment(
        client_name: str,
        service_type: str,
        appointment_date: str,
        notes: str = ""
):
    """Создать новую заявку"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO appointments (client_name, service_type, appointment_date, notes)
            VALUES (?, ?, ?, ?)
        ''', (client_name, service_type, appointment_date, notes))

        await db.commit()
        appointment_id = cursor.lastrowid

        # Возвращаем созданную заявку
        return await get_appointment_by_id(appointment_id)


async def update_appointment(
        appointment_id: int,
        client_name: str = None,
        service_type: str = None,
        appointment_date: str = None,
        notes: str = None
):
    """Обновить заявку"""
    # Проверяем существование заявки
    appointment = await get_appointment_by_id(appointment_id)
    if not appointment:
        return None

    # Собираем поля для обновления
    updates = []
    params = []

    if client_name is not None:
        updates.append("client_name = ?")
        params.append(client_name)

    if service_type is not None:
        updates.append("service_type = ?")
        params.append(service_type)

    if appointment_date is not None:
        updates.append("appointment_date = ?")
        params.append(appointment_date)

    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)

    if not updates:
        return appointment

    params.append(appointment_id)

    async with aiosqlite.connect(DB_PATH) as db:
        query = f"UPDATE appointments SET {', '.join(updates)} WHERE id = ?"
        await db.execute(query, params)
        await db.commit()

    return await get_appointment_by_id(appointment_id)


async def delete_appointment(appointment_id: int):
    """Удалить заявку"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем существование
        cursor = await db.execute(
            'SELECT id FROM appointments WHERE id = ?',
            (appointment_id,)
        )
        if not await cursor.fetchone():
            return False

        await db.execute(
            'DELETE FROM appointments WHERE id = ?',
            (appointment_id,)
        )
        await db.commit()
        return True


async def reschedule_appointment(appointment_id: int, new_date: str):
    """Перенести заявку на другую дату"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем существование
        cursor = await db.execute(
            'SELECT id FROM appointments WHERE id = ?',
            (appointment_id,)
        )
        if not await cursor.fetchone():
            return None

        await db.execute(
            'UPDATE appointments SET appointment_date = ? WHERE id = ?',
            (new_date, appointment_id)
        )
        await db.commit()

    return await get_appointment_by_id(appointment_id)