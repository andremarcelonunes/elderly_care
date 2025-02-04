from pydantic import BaseModel, EmailStr, Field, model_validator, StringConstraints, ConfigDict
from typing import Optional, Literal, List, Annotated, Dict
from datetime import date


# noinspection PyMethodParameters
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')  # Validação do phone
    role: Literal["contact", "subscriber", "assisted", "attendant"]
    active: Optional[bool] = True
    password: str = Field(..., min_length=8)  # Validação básica de tamanho mínimo
    client_data: Optional["SubscriberCreate"] = None
    client_ids: Optional[List[int]] = None  # Lista de IDs de clientes
    attendant_data: Optional["AttendantCreate"] = None

    @model_validator(mode="after")
    def validate_specialization(cls, values):
        role = values.role
        client_data = values.client_data
        client_ids = values.client_ids
        attendant_data = values.attendant_data

        if role == "subscriber" and not client_data:
            raise ValueError("client_data is required when role is 'subscriber'.")
        if role == "contact" and not client_ids:
            raise ValueError("client_ids (list of client IDs) is required when role is 'contact'.")
        if role == "attendant" and not attendant_data:
            raise ValueError("attendant_data is required when role is 'attendant'.")
        return values


class SubscriberCreate(BaseModel):
    cpf: str
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    code_address: Optional[str] = None
    birthday: date


class ContactCreate(BaseModel):
    user_client_id: int
    user_contact_id: int

class AssitedCreate(BaseModel):
    subscriber_id: int
    assisted_id: int


class AttendantCreate(BaseModel):
    function_id: Optional[int] = None
    team_id: Optional[int] = None


class UserSearch(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[Annotated[str, StringConstraints(strip_whitespace=True)]] = None
    cpf: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=11, max_length=14)]] = None

    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                # or
                "phone": "+123456789",
                # or
                "cpf": "123.456.789-00"
            }
        }


class SubscriberInfo(BaseModel):
    cpf: str
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    code_address: Optional[str] = None
    birthday: date
    model_config = ConfigDict(from_attributes=True)


class UserInfo(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    role: str
    active: Optional[bool] = True
    client_data: Optional[SubscriberInfo] = None
    model_config = ConfigDict(from_attributes=True)


class ClientUpdate(BaseModel):
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    code_address: Optional[str] = None

    @model_validator(mode="before")
    def check_extra_fields(cls, values):
        extra_fields = set(values.keys()) - set(cls.__fields__.keys())
        if extra_fields:
            raise ValueError("this change is not authorized")
        return values


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')  # Validação do phon
    active: Optional[bool] = None
    client_data: Optional[ClientUpdate] = None

    @model_validator(mode="before")
    def check_extra_fields(cls, values):
        extra_fields = set(values.keys()) - set(cls.__fields__.keys())
        if extra_fields:
            raise ValueError("this change is not authorized")
        return values


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    active: bool
    client_data: Optional[Dict] = None


UserCreate.model_rebuild()
