from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from backendeldery.models import (
    User, Attendant, Specialty, AttendantSpecialty
)

from backendeldery.schemas import (
    UserCreate,  AttendantCreate, AttendantResponse, AttendandInfo
)
from .users import CRUDUser
from .team import CRUDTeam
from .function import CRUDFunction
from .base import CRUDBase


class CRUDAttendant(CRUDBase[Attendant, AttendantCreate]):
    def __init__(self):
        super().__init__(Attendant)
        self.crud_user = CRUDUser()
        self.crud_function = CRUDFunction()
        self.crud_team = CRUDTeam()

    async def create(self, db: Session, obj_in, created_by: int, user_ip: str) -> Attendant:
        """
        Cria um novo usuário e attendant e registra informações de auditoria.
        """

        try:
            # Step 1: Create the User
            user = await self.crud_user.create(db, obj_in.dict(), created_by, user_ip)

            if obj_in.role == "attendant" and obj_in.attendant_data:
                # Create the Attendant using the User ID
                attendant_data = obj_in.attendant_data.model_dump()
                specialties_list = attendant_data.pop("specialties", [])
                # Debugging: Log the content of attendant_data

                # Ensure all necessary fields are included in attendant_data
                # Add the user_id, created_by, and user_ip fields to the dictionary
                attendant_data["user_id"] = user.id
                attendant_data["created_by"] = created_by
                attendant_data["user_ip"] = user_ip

                # Now create the Attendant instance using the provided fields
                try:
                    attendant = Attendant(**attendant_data)
                except TypeError as e:

                    raise HTTPException(status_code=400, detail=f"Error while creating Attendant: {e}")

                # Step 3: Add specialties if provided, avoiding duplicates
                if specialties_list:
                    for specialty_name in specialties_list:
                        # Try to find an existing specialty
                        specialty = db.query(Specialty).filter(Specialty.name == specialty_name).first()
                        if not specialty:
                            specialty = Specialty(
                                name=specialty_name,
                                created_by=created_by,
                                user_ip=user_ip,
                                updated_by=None
                            )
                            db.add(specialty)
                            db.flush()
                        # Create the association with audit data
                        association = AttendantSpecialty(
                            created_by=created_by,  # Use the endpoint provided user id
                            user_ip=user_ip
                        )
                        association.specialty = specialty
                        # Append the association to the attendant's association collection
                        attendant.specialty_associations.append(association)

                db.add(attendant)

                db.commit()  # Commit the transaction, saving both User and Attendant
                db.refresh(attendant)  # Retrieve the newly created attendant
                user.attendant = attendant  # Link the Attendant to the User
                db.commit()
                db.refresh(user)  # Refresh the user object to include the attendant

            db.commit()
            db.refresh(user)  # Ensure the user is fully created and returned
            if user.attendant:
                attendant_info = AttendantResponse.from_orm(user.attendant)
                # You can then attach this data to your user response model if desired:
                user_info = AttendandInfo.from_orm(user)
                # For example, if you want to store it in an attribute named "attendant_data":
                user_info.attendant_data = attendant_info
                return user_info

            return AttendandInfo.from_orm(user)

        except Exception as e:
            # Rollback the transaction if something goes wrong
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error to register Attendant: {str(e)}"
            )
