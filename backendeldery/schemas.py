from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    model_validator,
    StringConstraints,
    ConfigDict,
)
from typing import Optional, Literal, List, Annotated, Dict
from datetime import date, datetime


# noinspection PyMethodParameters
class UserCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None  # Optional by default.
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")  # Validação do phone
    role: Literal["contact", "subscriber", "assisted", "attendant"]
    active: Optional[bool] = True
    password: str = Field(..., min_length=8)  # Validação básica de tamanho mínimo
    client_data: Optional["SubscriberCreate"] = None
    client_ids: Optional[List[int]] = None  # Lista de IDs de clientes
    attendant_data: Optional["AttendantCreate"] = None

    @model_validator(mode="after")
    def validate_specialization(cls, model: "UserCreate") -> "UserCreate":
        if model.role == "subscriber":
            if model.client_data is None:
                raise ValueError("client_data is required when role is 'subscriber'.")
            if model.email is None:
                raise ValueError("email is required when role is 'subscriber'.")
        elif model.role == "contact":
            if not model.client_ids:
                raise ValueError(
                    "client_ids (list of client IDs) is required when role is 'contact'."
                )
        elif model.role == "attendant":
            if model.attendant_data is None:
                raise ValueError("attendant_data is required when role is 'attendant'.")
        return model


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


class AssistedCreate(BaseModel):
    subscriber_id: int
    assisted_id: int


class AttendantCreate(BaseModel):
    function_id: Optional[int] = None
    team_id: Optional[int] = None


class UserSearch(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[Annotated[str, StringConstraints(strip_whitespace=True)]] = None
    cpf: Optional[
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=11, max_length=14)
        ]
    ] = None

    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                # or
                "phone": "+123456789",
                # or
                "cpf": "123.456.789-00",
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
    email: Optional[EmailStr] = None  # Optional by default.
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
    phone: Optional[str] = Field(
        None, pattern=r"^\+?[1-9]\d{1,14}$"
    )  # Validação do phon
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

    model_config = ConfigDict(from_attributes=True)

class AssistedResponse(BaseModel):
    user_id: int
    # We expect the Client model to have an attribute "user" (the related User instance)
    # so we map the 'assisted' field to the "user" attribute using an alias.
    assisted: UserResponse = Field(..., alias="user")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


UserCreate.model_rebuild()
