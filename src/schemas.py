from pydantic import BaseModel, ConfigDict

from models import Gender
from validators import PersonName, PhoneNumber, Birthday


class EmployeeBase(BaseModel):
    first_name: PersonName
    last_name: PersonName
    middle_name: PersonName | None = None

    phone_number: PhoneNumber | None = None
    birthday: Birthday

    gender: Gender


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: PersonName | None = None
    last_name: PersonName | None = None
    middle_name: PersonName | None = None

    phone_number: PhoneNumber | None = None
    birthday: Birthday | None = None

    gender: Gender | None = None


class EmployeeResponse(EmployeeBase):
    id: int
    photo_path: str | None = None

    model_config = ConfigDict(from_attributes=True)
