from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, Literal, List
from datetime import date


class UserCreate(BaseModel):
    user_name: str
    user_email: EmailStr
    user_phone: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')  # Validação do telefone
    user_role: Literal["contact", "client", "attendant"]
    user_password: str = Field(..., min_length=8)  # Validação básica de tamanho mínimo
    user_birthday: Optional[date] = None
    client_data: Optional["ClientCreate"] = None
    client_ids: Optional[List[int]] = None  # Lista de IDs de clientes
    attendant_data: Optional["AttendantCreate"] = None

    @model_validator(mode="after")
    def validate_specialization(cls, values):
        role = values.user_role
        client_data = values.client_data
        client_ids = values.client_ids
        attendant_data = values.attendant_data

        if role == "client" and not client_data:
            raise ValueError("client_data is required when user_role is 'client'.")
        if role == "contact" and not client_ids:
            raise ValueError("client_ids (list of client IDs) is required when user_role is 'contact'.")
        if role == "attendant" and not attendant_data:
            raise ValueError("attendant_data is required when user_role is 'attendant'.")
        return values


class ClientCreate(BaseModel):
    client_address: str
    client_neighborhood: str
    client_city: str
    client_state: str
    client_code_address: str  # Agora obrigatório


class ContactCreate(BaseModel):
    user_client_id: int
    user_contact_id: int


class AttendantCreate(BaseModel):
    function_id: Optional[int] = None
    team_id: Optional[int] = None