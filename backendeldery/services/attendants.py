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

    @staticmethod
    async def update(db, user_id, user_update, user_ip, updated_by):
        """
        Updates an attendant's information in the system.

        Parameters:
            db: Database session instance used for database operations.
            user_id: Unique identifier of the attendant to update.
            user_update: Data containing updated user information.
            user_ip: IP address from which the update request originated.
            updated_by: Identifier of the user performing the update.

        Returns:
            The updated attendant record.
        """
        try:
            await CRUDAttendant().update(db, user_id, user_update, updated_by, user_ip)
            updated_attendant = await CRUDAttendant().get_async(db, user_id)
            if not updated_attendant:
                raise HTTPException(status_code=404, detail="Attendant not found")
            return updated_attendant  # Already in final form.
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error on updating: {str(e)}")
