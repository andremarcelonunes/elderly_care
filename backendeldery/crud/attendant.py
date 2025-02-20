from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from backendeldery.models import (
    User, Attendant, Specialty
)

from backendeldery.schemas import (
    UserCreate, AttendantCreate
)
from .users import CRUDUser
from .base import CRUDBase
import logging

logger = logging.getLogger("backendeldery")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)


class CRUDAttendant(CRUDBase[Attendant, AttendantCreate]):
    def __init__(self):
        super().__init__(Attendant)
        self.crud_user = CRUDUser()

    async def create(self, db: Session,
                     obj_in: UserCreate,
                     created_by: int, user_ip: str) -> Attendant:
        """
        Cria um novo usuário e attendant e registra informações de auditoria.
        """
        logger.info("Iniciando criação do user e attendant...")

        try:
            # Step 1: Create the User
            user = await self.crud_user.create(db, obj_in.dict(), created_by, user_ip)

            if obj_in.role == "attendant" and obj_in.attendant_data:
                # Create the Attendant using the User ID
                attendant_data = obj_in.attendant_data.model_dump()
                specialties_list = attendant_data.pop("specialties", [])
                # Debugging: Log the content of attendant_data
                logger.info(f"Attendant data before creating Attendant: {attendant_data}")

                # Ensure all necessary fields are included in attendant_data
                # Add the user_id, created_by, and user_ip fields to the dictionary
                attendant_data["user_id"] = user.id
                attendant_data["created_by"] = created_by
                attendant_data["user_ip"] = user_ip

                # Now create the Attendant instance using the provided fields
                try:
                    attendant = Attendant(**attendant_data)
                except TypeError as e:
                    # Catch and log if the fields are missing or incorrect
                    logger.error(f"Error while creating Attendant: {e}")
                    raise HTTPException(status_code=500, detail=f"Error while creating Attendant: {e}")

                # Step 3: Add specialties if provided, avoiding duplicates
                if specialties_list:
                    for specialty_name in specialties_list:
                        specialty = db.query(Specialty).filter(Specialty.name == specialty_name).first()
                        if not specialty:
                            specialty = Specialty(name=specialty_name)
                            db.add(specialty)
                            db.flush()
                        attendant.specialties.append(specialty)

                db.add(attendant)

                db.commit()  # Commit the transaction, saving both User and Attendant
                db.refresh(attendant)  # Retrieve the newly created attendant

            db.commit()
            db.refresh(user)  # Ensure the user is fully created and returned
            return user

        except Exception as e:
            # Rollback the transaction if something goes wrong
            db.rollback()
            logger.error(f"Erro durante a criação do user e attendant: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error to register Attendant: {str(e)}"
            )
