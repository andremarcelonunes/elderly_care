from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery.crud.attendant import CRUDAttendant
from backendeldery.schemas import UserCreate
from backendeldery.validators.attendant_validator import AttendantValidator
from backendeldery.validators.user_validator import UserValidator


class AttendantService:
    @staticmethod
    async def create_attendant(
        db: Session, user_data: UserCreate, created_by: int, user_ip: str
    ):
        """
        Registers an attendant in the system.
        """
        validator = AttendantValidator()
        try:
            # Validate the attendant data using the model instance (not a dict)
            UserValidator.validate_user(db, user_data)
            validator.validate_attendant(db, user_data.attendant_data)
            # Call the CRUD method to create the attendant
            return await CRUDAttendant().create(
                db=db,
                obj_in=user_data,
                created_by=created_by,
                user_ip=user_ip,
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def get_attendant_by_id(db: Session, id: int) -> Optional[dict]:
        """
        Fetches an attendant by ID with user details if they exist.
        """
        try:
            return await CRUDAttendant().get(db, id)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
