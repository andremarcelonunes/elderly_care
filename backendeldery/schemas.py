from datetime import date, datetime
from typing import Annotated, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    model_validator,
)

# from email_validator import validate_email, EmailNotValidError
from backendeldery.validators.cpf_validator import CPFValidator


# noinspection PyMethodParameters
class UserCreate(BaseModel):
    name: Annotated[str, StringConstraints(max_length=200)]
    email: EmailStr = Field(default=None, mode="strict")  # Optional email field
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    receipt_type: Literal[1, 2, 3]
    role: Literal["contact", "subscriber", "assisted", "attendant"]
    active: bool | None = True
    password: str | None = Field(None, min_length=8)  # Now optional.
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

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class SubscriberCreate(BaseModel):
    cpf: CPFValidator
    team_id: int | None = None
    address: Annotated[str, StringConstraints(max_length=200)]
    neighborhood: Annotated[str, StringConstraints(max_length=100)]
    city: Annotated[str, StringConstraints(max_length=100)]
    state: Annotated[str, StringConstraints(max_length=100)]
    code_address: Annotated[str, StringConstraints(max_length=9)]
    birthday: date

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class ContactCreate(BaseModel):
    user_client_id: int
    user_contact_id: int


class AssistedCreate(BaseModel):
    subscriber_id: int
    assisted_id: int


class AttendantCreate(BaseModel):
    cpf: CPFValidator
    address: Annotated[str, StringConstraints(max_length=100)]
    neighborhood: Annotated[str, StringConstraints(max_length=100)]
    city: Annotated[str, StringConstraints(max_length=100)]
    state: Annotated[str, StringConstraints(max_length=100)]
    code_address: Annotated[str, StringConstraints(max_length=9)]
    birthday: date
    registro_conselho: Annotated[str, StringConstraints(max_length=20)]
    nivel_experiencia: Literal["junior", "pleno", "senior", "especialista"]
    formacao: Annotated[str, StringConstraints(max_length=100)]
    specialties: list[str] | None = []
    team_names: list[str] | None = []
    function_names: str | None = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AttendantResponse(BaseModel):
    cpf: str
    address: str | None = None
    neighborhood: str | None = None
    city: str | None = None
    state: str | None = None
    code_address: str | None = None
    birthday: date
    registro_conselho: str | None = None
    nivel_experiencia: str  # You could further restrict with Literal if needed
    formacao: str | None = None
    specialty_names: list[str]
    team_names: list[str] = []
    function_names: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserSearch(BaseModel):
    email: EmailStr | None = Field(None, mode="strict")
    phone: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=15)] | None
    ) = None
    cpf: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=11, max_length=14)
        ]
        | None
    ) = None

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
    team_id: int | None = None
    address: str | None = None
    neighborhood: str | None = None
    city: str | None = None
    state: str | None = None
    code_address: str | None = None
    birthday: date | None = None
    model_config = ConfigDict(from_attributes=True)


class UserInfo(BaseModel):
    id: int
    name: str
    email: EmailStr | None = None  # Optional by default.
    phone: str
    receipt_type: int | None = None
    role: str
    active: bool | None = True
    client_data: SubscriberInfo | None = None
    attendant_data: AttendantResponse | None = None
    model_config = ConfigDict(from_attributes=True)


class AttendandInfo(BaseModel):
    id: int
    name: str
    email: EmailStr | None = None  # Optional by default.
    phone: str
    receipt_type: int | None = None
    role: str
    active: bool | None = True
    attendant_data: AttendantResponse | None = None
    model_config = ConfigDict(from_attributes=True)


class ClientUpdate(BaseModel):
    team_id: int | None = None
    address: str | None = None
    neighborhood: str | None = None
    city: str | None = None
    state: str | None = None
    code_address: str | None = None

    @model_validator(mode="before")
    def check_extra_fields(cls, values):
        extra_fields = set(values.keys()) - set(cls.__fields__.keys())
        if extra_fields:
            raise ValueError("this change is not authorized")
        return values

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AttendantUpdate(BaseModel):
    address: Annotated[str, StringConstraints(max_length=100)]
    neighborhood: Annotated[str, StringConstraints(max_length=100)]
    city: Annotated[str, StringConstraints(max_length=100)]
    state: Annotated[str, StringConstraints(max_length=100)]
    code_address: Annotated[str, StringConstraints(max_length=9)]
    registro_conselho: Annotated[str, StringConstraints(max_length=20)]
    nivel_experiencia: Literal["junior", "pleno", "senior", "especialista"] | None = (
        None
    )
    formacao: Annotated[str, StringConstraints(max_length=100)]
    specialties: list[str] | None = []
    team_names: list[str] | None = []
    function_names: str | None = None

    @model_validator(mode="before")
    def check_extra_fields(cls, values):
        extra_fields = set(values.keys()) - set(cls.model_fields.keys())
        if extra_fields:
            raise ValueError("this change is not authorized")
        return values

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserUpdate(BaseModel):
    email: EmailStr | None = Field(None, mode="strict")
    phone: str | None = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")  # Validação do phone
    receipt_type: int | None = None
    active: bool | None = None
    client_data: ClientUpdate | None = None
    attendant_data: AttendantUpdate | None = None

    @model_validator(mode="before")
    def check_extra_fields(cls, values):
        extra_fields = set(values.keys()) - set(cls.__fields__.keys())
        if extra_fields:
            raise ValueError("this change is not authorized")
        return values

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserResponse(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str
    receipt_type: int
    role: str
    active: bool
    client_data: dict | None = None
    attendant_data: dict | None = None

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        return {k: v for k, v in data.items() if v is not None}

    model_config = ConfigDict(from_attributes=True)


class AssistedUserResponse(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str
    receipt_type: int
    role: str
    active: bool
    client_data: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class AssistedResponse(BaseModel):
    user_id: int
    assisted: AssistedUserResponse = Field(..., alias="user")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AttendantData(BaseModel):
    cpf: str
    birthday: date | None = None
    address: str | None = None
    neighborhood: str | None = None
    city: str | None = None
    state: str | None = None
    code_address: str | None = None
    registro_conselho: str | None = None
    nivel_experiencia: str | None = None
    formacao: str | None = None
    user_ip: str | None = None
    function_id: int | None = None
    # Usamos alias para mapear a propriedade híbrida specialty_names para specialties
    specialties: list[str] = Field(default_factory=list, alias="specialty_names")
    team_names: list[str] = Field(default_factory=list)
    function_names: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AttendantTimeResponse(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str
    receipt_type: int | None = None
    role: str
    active: bool
    attendant_data: AttendantData | None = None

    model_config = ConfigDict(from_attributes=True)


UserCreate.model_rebuild()
