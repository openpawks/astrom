import pytest
from httpx import AsyncClient, ASGITransport
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import io

from database import get_db, Base
from main import app
import models

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


@pytest.fixture(autouse=True)
async def init_db():
    """Перед каждым тестом создаем чистые таблицы в базе, а после теста всё удаляем"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    """Подменяем реальную базу данных на тестовую на время проверки"""
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.mark.asyncio
async def test_create_employee_success():
    """Проверяем, что новый сотрудник успешно добавляется через форму"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        form_data = {
            "first_name": "Иван",
            "last_name": "Иванов",
            "middle_name": "Иванович",
            "phone_number": "+79254455667",
            "birthday": "1995-05-15",
            "gender": "Мужчина",
        }
        response = await ac.post("/employees/", data=form_data)

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Иван"
        assert data["id"] is not None


@pytest.mark.asyncio
async def test_create_employee_with_photo():
    """Проверяем, что загрузка аватарки работает и файл сохраняется куда нужно"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        form_data = {
            "first_name": "Коля",
            "last_name": "Петров",
            "birthday": "1990-01-01",
            "gender": "Мужчина",
        }
        file_payload = {
            "photo": ("avatar.png", io.BytesIO(b"fake-image-bytes"), "image/png")
        }

        response = await ac.post("/employees/", data=form_data, files=file_payload)

        assert response.status_code == 201
        data = response.json()
        assert data["photo_path"] is not None
        assert data["photo_path"].startswith("photos/")


@pytest.mark.asyncio
async def test_create_employee_missing_required_birthday():
    """Проверяем, что система выдаст ошибку, если забыть указать дату рождения"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        bad_form_data = {
            "first_name": "Анна",
            "last_name": "Сидорова",
            "gender": "Женщина",
        }
        response = await ac.post("/employees/", data=bad_form_data)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_registry_data_context():
    """Проверяем, что созданный сотрудник появляется в списке всех сотрудников"""
    async with TestingSessionLocal() as session:
        emp = models.Employee(
            first_name="Мария",
            last_name="Новикова",
            birthday=date(2000, 12, 12),
            gender=models.Gender.female,
        )
        session.add(emp)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/employees/")
        assert response.status_code == 200

        data = response.json()
        assert any(e["last_name"] == "Новикова" for e in data)


@pytest.mark.asyncio
async def test_delete_employee():
    """Проверяем, что сотрудник действительно удаляется из базы и больше не находится"""
    async with TestingSessionLocal() as session:
        emp = models.Employee(
            first_name="Олег",
            last_name="Волков",
            birthday=date(1988, 8, 8),
            gender=models.Gender.male,
        )
        session.add(emp)
        await session.commit()
        await session.refresh(emp)
        emp_id = emp.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        del_response = await ac.delete(f"/employees/{emp_id}")
        assert del_response.status_code == 204

        get_response = await ac.get(f"/employees/{emp_id}")
        assert get_response.status_code == 404
