from pydantic import BaseModel, EmailStr,  Field, model_validator
from typing import Optional, List, Literal
from datetime import date
from pydantic import BaseModel, Field, EmailStr, model_validator
from typing import Optional, Literal
from datetime import date


class UserCreate(BaseModel):
    user_name: str
    user_email: EmailStr
    user_phone: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')  # Validação do telefone
    user_role: Literal["contact", "client", "attendant"]
    user_password: str = Field(..., min_length=8)  # Validação básica de tamanho mínimo
    user_birthday: Optional[date] = None

    @model_validator(mode="after")  # Substitui o @root_validator
    def validate_password(cls, values):
        password = values.user_password
        if password:
            if not any(char.isupper() for char in password):
                raise ValueError("Password must contain at least one uppercase letter.")
            if not any(char.isdigit() for char in password):
                raise ValueError("Password must contain at least one number.")
            if not any(char in "@$!%*?&" for char in password):
                raise ValueError("Password must contain at least one special character (@$!%*?&).")
        return values
    class Config:
        json_schema_extra = {
            "example": {
                "user_name": "John Doe",
                "user_email": "john.doe@example.com",
                "user_phone": "+123456789",
                "user_role": "client",
                "user_password": "Strong@123",
                "user_birthday": "1990-01-01",
            }
        }


class UserResponse(BaseModel):
    user_id: int
    user_name: str
    user_email: EmailStr
    user_phone: str
    user_role: str
    user_birthday: Optional[date] = None

    class Config:
        from_attributes = True

