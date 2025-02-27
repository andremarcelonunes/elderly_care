import logging

from fastapi import HTTPException
from sqlalchemy import cast, String
from sqlalchemy.orm import Session

from backendeldery.models import (
    Attendant,
    Specialty,
    AttendantSpecialty,
    AttendantTeam,
)
from backendeldery.schemas import (
    AttendantCreate,
    AttendantResponse,
    AttendandInfo,
)
from .base import CRUDBase
from .function import CRUDFunction
from .team import CRUDTeam
from .users import CRUDUser

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
        self.crud_function = CRUDFunction()
        self.crud_team = CRUDTeam()

    async def create(
        self, db: Session, obj_in, created_by: int, user_ip: str
    ) -> Attendant:
        logger.info("Creating attendant")
        try:
            # Step 1: Create the User
            user = await self.crud_user.create(db, obj_in.dict(), created_by, user_ip)
            logger.info(f"User created: %s", user)
            if obj_in.role == "attendant" and obj_in.attendant_data:
                attendant_data = obj_in.attendant_data.model_dump()
                specialties_list = attendant_data.pop("specialties", [])
                team_names = attendant_data.pop("team_names", [])
                function_name = attendant_data.pop("function_names", None)
                attendant_data["user_id"] = user.id
                attendant_data["created_by"] = created_by
                attendant_data["user_ip"] = user_ip

                # Now create the Attendant instance using the provided fields
                try:
                    attendant = Attendant(**attendant_data)
                except TypeError as e:
                    raise HTTPException(
                        status_code=400, detail=f"Error while creating Attendant: {e}"
                    )

                # Step 3: Add specialties if provided, avoiding duplicates
                if specialties_list:
                    for specialty_name in specialties_list:
                        specialty = (
                            db.query(Specialty)
                            .filter(cast(Specialty.name, String) == specialty_name)
                            .first()
                        )
                        if not specialty:
                            specialty = Specialty(
                                name=specialty_name,
                                created_by=created_by,
                                user_ip=user_ip,
                                updated_by=None,
                            )
                            db.add(specialty)
                            db.flush()
                        association = AttendantSpecialty(
                            created_by=created_by,
                            user_ip=user_ip,
                        )
                        association.specialty = specialty
                        attendant.specialty_associations.append(association)
                        db.add(
                            association
                        )  # Ensure the association is tracked by the session
                if team_names:
                    logger.info(f"Printing team_names: %s", team_names)
                    for t_name in team_names:
                        team = await self.crud_team.get_by_name(db, t_name)
                        logger.info(f"Return get_by_name: %s", team)
                        if not team:
                            team = await self.crud_team.create(
                                db,
                                t_name,
                                team_site="default",
                                created_by=created_by,
                                user_ip=user_ip,
                            )
                            logger.info(f"Return team.create: %s", team)
                        # Always create a new AttendantTeam instance:
                        team_association = AttendantTeam(
                            team=team, created_by=created_by, user_ip=user_ip
                        )
                        logger.info(f"Adding Association: %s", team_association)
                        attendant.team_associations.append(team_association)
                        db.add(team_association)

                if function_name:
                    logger.info(f"Printing functions: %s", function_name)
                    func_obj = await self.crud_function.get_by_name(db, function_name)
                    logger.info(f"Return get_by_name: %s", func_obj)
                    if not func_obj:
                        func_obj = await self.crud_function.create(
                            db,
                            function_name,
                            description="Auto-created function",
                            created_by=created_by,
                            user_ip=user_ip,
                        )
                        logger.info(f"Return function.create: %s", func_obj)
                    attendant.function = func_obj

                db.add(attendant)
                db.commit()
                db.refresh(attendant)
                user.attendant = attendant
                db.commit()
                db.refresh(user)

            db.commit()
            db.refresh(user)
            if user.attendant:
                attendant_info = AttendantResponse.from_orm(user.attendant)
                user_info = AttendandInfo.from_orm(user)
                user_info.attendant_data = attendant_info
                user_info.attendant_data.team_names = [
                    team.team_name for team in user.attendant.teams
                ]
                user_info.attendant_data.function_names = (
                    user.attendant.function.name if user.attendant.function else None
                )
                logger.info(f"Return user_info: %s", user_info)
                return user_info

            return AttendandInfo.from_orm(user)

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error to register Attendant: {str(e)}"
            )
