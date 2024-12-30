from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List, Literal
from datetime import date

class UserCreate(BaseModel):
    user_name: str
    user_email: EmailStr
    user_phone: str
    user_role: Literal["contact", "client", "attendand"]
    user_password: constr(min_length=8)
    user_birthday: Optional[date] = None

class ClientCreate(BaseModel):
    user_id: int
    team_id: int = None  # Opcional (nullable=True)
    user_address: str
    user_neighborhood: str
    user_city: str
    user_state: str
    user_code_address: constr(regex=r'^\d{5}-\d{3}$')


class ContactCreate(BaseModel):
    user_client_id: int
    user_contact_id: int

class NotificationConfigUpdate(BaseModel):
    notify_level: Optional[int] = 1

class TeamCreate(BaseModel):
    team_name: str  # Obrigatório (nullable=False)

class ContactCreateMany(BaseModel):
    contacts: List[ContactCreate]

class AttendandCreate(BaseModel):
    user_id: int
    team_id: int
    attendant_function: Literal["nurse", "doctor", "assistant"]
