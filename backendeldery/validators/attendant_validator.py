from fastapi import HTTPException
from sqlalchemy.orm import Session
from backendeldery.models import (
    User,
    Attendant,

)
from backendeldery.schemas import UserCreate, AttendantCreate


class AttendantValidator:
    def validate_attendant(db: Session, user: UserCreate, attendant_data: AttendantCreate):
        """
        Validates the Attendant data before creating a new attendant.
        """
        if db.query(Attendant).filter(Attendant.cpf == attendant_data.cpf).first():
            raise HTTPException(status_code=422, detail="CPF already exists")



