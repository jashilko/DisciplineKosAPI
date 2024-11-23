from pydantic import BaseModel, EmailStr, Field, validator
import re


class SUserRegister(BaseModel):
    public_name: str = Field(..., min_length=3, max_length=50, description="Фамилия, от 3 до 50 символов")
    first_name: str = Field(..., min_length=3, max_length=50, description="Имя, от 3 до 50 символов")
    email: EmailStr = Field(..., description="Электронная почта")
    password: str = Field(..., min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")
