from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from uuid import uuid4
from pathlib import Path
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
import models
from schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse


PHOTO_DIR = Path("data/photos")
PHOTO_DIR.mkdir(parents=True, exist_ok=True)


def get_employee_create(
    first_name: str = Form(...),
    last_name: str = Form(...),
    middle_name: str | None = Form(None),
    phone_number: str | None = Form(None),
    birthday: str = Form(...),
    gender: models.Gender = Form(...),
) -> EmployeeCreate:
    return EmployeeCreate(
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
        phone_number=phone_number,
        birthday=date.fromisoformat(birthday),
        gender=gender,
    )


def get_employee_partial(
    first_name: str | None = Form(None),
    last_name: str | None = Form(None),
    middle_name: str | None = Form(None),
    phone_number: str | None = Form(None),
    birthday: str | None = Form(None),
    gender: models.Gender | None = Form(None),
):
    return EmployeeUpdate(
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
        phone_number=phone_number,
        birthday=date.fromisoformat(birthday),
        gender=gender,
    )


async def save_photo(photo: UploadFile | None) -> str | None:
    if not photo:
        return None

    ext = Path(photo.filename).suffix
    filename = f"{uuid4().hex}{ext}"
    path = PHOTO_DIR / filename

    with path.open("wb") as f:
        f.write(await photo.read())

    return f"photos/{filename}"


router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(
    employee_data: Annotated[EmployeeCreate, Depends(get_employee_create)],
    db: Annotated[AsyncSession, Depends(get_db)],
    photo: UploadFile | None = File(default=None),
):
    photo_path = None

    if photo:
        photo_path = await save_photo(photo)

    employee = models.Employee(
        **employee_data.model_dump(),
        photo_path=photo_path,
    )

    db.add(employee)

    await db.commit()
    await db.refresh(employee)

    return employee


@router.get(
    "/",
    response_model=list[EmployeeResponse],
)
async def get_employees(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.Employee))
    employees = result.scalars().all()
    return employees


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
async def get_employee(
    employee_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.Employee).where(models.Employee.id == employee_id)
    )
    employee = result.scalars().first()

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return employee


@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
async def update_employee_partial(
    employee_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    employee_data: Annotated[EmployeeUpdate, Depends(get_employee_partial)],
    photo: UploadFile | None = File(default=None),
):
    result = await db.execute(
        select(models.Employee).where(models.Employee.id == employee_id)
    )
    employee = result.scalars().first()

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    update_data = employee_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(employee, field, value)

    if photo:
        employee.photo_path = await save_photo(photo)

    await db.commit()
    await db.refresh(employee)

    return employee


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_employee(
    employee_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.Employee).where(models.Employee.id == employee_id)
    )
    employee = result.scalars().first()

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    await db.delete(employee)
    await db.commit()
