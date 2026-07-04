import re

from datetime import date
from typing import Annotated

from pydantic.functional_validators import AfterValidator

PHONE_REGEX = re.compile(r"^\+\d{7,15}$")


def validate_name(value: str) -> str:
    value = value.strip()

    if not value:
        raise ValueError("Name cannot be empty.")

    if any(char.isdigit() for char in value):
        raise ValueError("Name cannot contain digits.")

    return value


def validate_phone(value: str) -> str:
    if not PHONE_REGEX.fullmatch(value):
        raise ValueError("Phone number must be in E.164 format (e.g. +447700900123).")
    return value


def validate_birthday(value: date) -> date:
    today = date.today()

    if value > today:
        raise ValueError("Birthday cannot be in the future.")

    if value.year < today.year - 120:
        raise ValueError("Birthday is unrealistically old.")

    return value


PersonName = Annotated[str, AfterValidator(validate_name)]
PhoneNumber = Annotated[str, AfterValidator(validate_phone)]
Birthday = Annotated[date, AfterValidator(validate_birthday)]
