import enum

from datetime import date, datetime

from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Integer, DateTime, Enum, func

from database import Base


class Gender(str, enum.Enum):
    male = "Мужчина"
    female = "Женщина"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    middle_name: Mapped[str | None] = mapped_column(String(50))

    phone_number: Mapped[str | None] = mapped_column(String(20))

    birthday: Mapped[date]

    gender: Mapped[Gender] = mapped_column(Enum(Gender))

    photo_path: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
