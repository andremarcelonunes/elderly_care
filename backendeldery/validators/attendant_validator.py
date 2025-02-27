from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery.models import (
    Attendant,
)
from backendeldery.schemas import AttendantCreate


class AttendantValidator:
    def validate_attendant(self, db: Session, attendant_data: AttendantCreate) -> None:
        """
        Validates the Attendant data before creating a new attendant.
        """
        if db.query(Attendant).filter(Attendant.cpf == attendant_data.cpf).first():
            raise HTTPException(status_code=422, detail="CPF already exists")
