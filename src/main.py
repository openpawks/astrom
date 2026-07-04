from contextlib import asynccontextmanager

from pathlib import Path

from typing import Annotated

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from database import engine, Base, get_db

import models

from schemas import EmployeeResponse

from routers import employees


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.mount("/photos", StaticFiles(directory="data/photos"), name="photos")

app.include_router(employees.router)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def employees_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.Employee))
    employees = result.scalars().all()

    employees_data = [
        EmployeeResponse.model_validate(e).model_dump(mode="json") for e in employees
    ]

    return templates.TemplateResponse(
        request,
        "employees.html",
        {"request": request, "employees": employees_data},
    )


@app.get("/new", response_class=HTMLResponse)
async def new_employee_page(request: Request):
    return templates.TemplateResponse(
        request,
        "employee_form.html",
        {"request": request, "employee": None},
    )


@app.get("/{employee_id}/edit", response_class=HTMLResponse)
async def edit_employee_page(
    employee_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.Employee).where(models.Employee.id == employee_id)
    )
    employee = result.scalars().first()

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    return templates.TemplateResponse(
        request,
        "employee_form.html",
        {"request": request, "employee": employee},
    )
