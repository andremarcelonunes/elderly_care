from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    model_validator,
    StringConstraints,
    ConfigDict,
)
from typing import Optional, Literal, Annotated, Dict, List
from datetime import date, datetime


# noinspection PyMethodParameters
class UserCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None  # Remains optional by default.
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    role: Literal["contact", "subscriber", "assisted", "attendant"]
    active: Optional[bool] = True
    password: Optional[str] = Field(None, min_length=8)  # Now optional.
    client_data: Optional["SubscriberCreate"] = None
    attendant_data: Optional["AttendantCreate"] = None

    @model_validator(mode="after")
    def validate_specialization(cls, model: "UserCreate") -> "UserCreate":
        if model.role == "subscriber":
            if model.client_data is None:
                raise ValueError("client_data is required when role is 'subscriber'.")
            if model.email is None:
                raise ValueError("email is required when role is 'subscriber'.")
            if model.password is None:
                raise ValueError("password is required when role is 'subscriber'.")
        elif model.role == "attendant":
            if model.attendant_data is None:
                raise ValueError("attendant_data is required when role is 'attendant'.")
            if model.email is None:
                raise ValueError("email is required when role is 'attendant'.")
            if model.password is None:
                raise ValueError("password is required when role is 'attendant'.")
        # For roles "assisted" and "contact", email and password may be omitted.
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
    cpf: str
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    code_address: Optional[str] = None
    birthday: date
    registro_conselho: Optional[str] = None
    nivel_experiencia: Literal["junior", "pleno", "senior", "especialista"]
    formacao: Optional[str] = None
    specialties: Optional[List[str]] = []

    model_config = ConfigDict(from_attributes=True)


class AttendantResponse(BaseModel):
    cpf: str
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    code_address: Optional[str] = None
    birthday: date
    registro_conselho: Optional[str] = None
    nivel_experiencia: str  # You could further restrict with Literal if needed
    formacao: Optional[str] = None
    specialty_names: List[str]

    model_config = ConfigDict(from_attributes=True)


class UserSearch(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[Annotated[str, StringConstraints(strip_whitespace=True)]] = None
    cpf: Optional[
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=11, max_length=14)
        ]
    ] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "phone": "+123456789",
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
    birthday: Optional[date] = None
    model_config = ConfigDict(from_attributes=True)


class UserInfo(BaseModel):
    id: int
    name: str
    email: Optional[EmailStr] = None  # Optional by default.
    phone: str
    role: str
    active: Optional[bool] = True
    client_data: Optional[SubscriberInfo] = None
    attendant_data: Optional[AttendantResponse] = None
    model_config = ConfigDict(from_attributes=True)


class AttendandInfo(BaseModel):
    id: int
    name: str
    email: Optional[EmailStr] = None  # Optional by default.
    phone: str
    role: str
    active: Optional[bool] = True
    attendant_data: Optional[AttendantResponse] = None
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
    email: Optional[str] = None
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
