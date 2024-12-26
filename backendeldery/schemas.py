from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# Usuários
class UserCreate(BaseModel):
    name: str
    email: str
    phone: str
    role: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    role: str

# Pacientes
class PatientCreate(BaseModel):
    user_id: int
    medical_conditions: Optional[str]

class PatientUpdate(BaseModel):
    medical_conditions: Optional[str]
    notify_contacts: Optional[bool]
    notify_nurses: Optional[bool]

class PatientResponse(BaseModel):
    id: int
    user_id: int
    medical_conditions: Optional[str]
    notify_contacts: bool
    notify_nurses: bool

# Contatos
class ContactCreate(BaseModel):
    patient_id: int
    contact_id: int

# Emergências
class EmergencyCreate(BaseModel):
    patient_id: int
    location: Optional[str]
    details: Dict[str, Any]

class EmergencyUpdate(BaseModel):
    status: str

class EmergencyResponse(BaseModel):
    id: str
    patient_id: int
    location: Optional[str]
    details: Dict[str, Any]
    status: str
    timestamp: str