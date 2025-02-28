import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backendeldery.models import (
    Attendant,
    Specialty,
    AttendantSpecialty,
    AttendantTeam,
    User,
)
from backendeldery.schemas import (
    AttendantResponse,
    AttendandInfo,
    UserInfo,
)
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


class CRUDAttendant(CRUDUser):
    def __init__(self):
        super().__init__()
        self.crud_function = CRUDFunction()
        self.crud_team = CRUDTeam()

    async def create(
        self, db: Session, obj_in, created_by: int, user_ip: str
    ) -> AttendandInfo:
        logger.info("Creating attendant")
        try:
            # Step 1: Create the User
            user = await super().create(db, obj_in.dict(), created_by, user_ip)
            logger.info("User created: %s", user)

            # Step 2: Process attendant data if needed
            if obj_in.role == "attendant" and obj_in.attendant_data:
                try:
                    attendant = await self._create_attendant(
                        db, obj_in.attendant_data, user.id, created_by, user_ip
                    )
                    user.attendant = attendant
                    self._commit_and_refresh(db, attendant, user)
                except TypeError as e:
                    db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error while creating Attendant: {str(e)}",
                    )

            # Step 3: Finalize user commit and build response
            self._finalize_user(db, user)
            return self._build_response(user)

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error to register Attendant: {str(e)}"
            )

    async def _create_attendant(
        self, db: Session, attendant_input, user_id: int, created_by: int, user_ip: str
    ) -> Attendant:
        try:
            # Extract attendant data and associated lists/names
            attendant_data = attendant_input.model_dump()
            specialties_list = attendant_data.pop("specialties", [])
            team_names = attendant_data.pop("team_names", [])
            function_name = attendant_data.pop("function_names", None)

            attendant_data.update(
                {
                    "user_id": user_id,
                    "created_by": created_by,
                    "user_ip": user_ip,
                }
            )

            attendant = Attendant(**attendant_data)

            # Add sub-associations
            self._add_specialties(db, attendant, specialties_list, created_by, user_ip)
            await self._add_team_associations(
                db, attendant, team_names, created_by, user_ip
            )
            await self._set_function_association(
                db, attendant, function_name, created_by, user_ip
            )

            db.add(attendant)
            return attendant

        except TypeError as e:
            raise HTTPException(
                status_code=400, detail=f"Error while creating Attendant: {str(e)}"
            )

    def _add_specialties(
        self,
        db: Session,
        attendant: Attendant,
        specialties_list: list,
        created_by: int,
        user_ip: str,
    ):
        for specialty_name in specialties_list:
            specialty = (
                db.query(Specialty).filter(Specialty.name == specialty_name).first()
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
            db.add(association)

    async def _add_team_associations(
        self,
        db: Session,
        attendant: Attendant,
        team_names: list,
        created_by: int,
        user_ip: str,
    ):
        logger.info("Team names: %s", team_names)
        for t_name in team_names:
            team = await self.crud_team.get_by_name(db, t_name)
            logger.info("Team returned from get_by_name: %s", team)
            if not team:
                team = await self.crud_team.create(
                    db,
                    t_name,
                    team_site="default",
                    created_by=created_by,
                    user_ip=user_ip,
                )
                logger.info("Team created: %s", team)
            team_association = AttendantTeam(
                team=team, created_by=created_by, user_ip=user_ip
            )
            logger.info("Adding team association: %s", team_association)
            attendant.team_associations.append(team_association)
            db.add(team_association)

    async def _set_function_association(
        self,
        db: Session,
        attendant: Attendant,
        function_name: str,
        created_by: int,
        user_ip: str,
    ):
        if function_name:
            logger.info("Processing function: %s", function_name)
            func_obj = await self.crud_function.get_by_name(db, function_name)
            logger.info("Function returned from get_by_name: %s", func_obj)
            if not func_obj:
                func_obj = await self.crud_function.create(
                    db,
                    function_name,
                    description="Auto-created function",
                    created_by=created_by,
                    user_ip=user_ip,
                )
                logger.info("Function created: %s", func_obj)
            attendant.function = func_obj

    def _commit_and_refresh(self, db: Session, attendant: Attendant, user):
        db.commit()
        db.refresh(attendant)
        user.attendant = attendant
        db.commit()
        db.refresh(user)

    def _finalize_user(self, db: Session, user):
        db.commit()
        db.refresh(user)

    def _build_response(self, user) -> AttendandInfo:
        if user.attendant:
            attendant_info = AttendantResponse.model_validate(user.attendant)
            user_info = AttendandInfo.model_validate(user)
            user_info.attendant_data = attendant_info
            user_info.attendant_data.team_names = [
                team.team_name for team in user.attendant.teams
            ]
            user_info.attendant_data.function_names = (
                user.attendant.function.name if user.attendant.function else None
            )
            logger.info("Returning user_info: %s", user_info)
            return user_info
        return AttendandInfo.model_validate(user)

    async def get(self, db: Session, id: int) -> Optional[UserInfo]:
        """
        Fetches an attendant by ID with user details if they exist.
        """
        try:
            user = (
                db.query(self.model)
                .options(
                    joinedload(User.attendant_data)
                )  # Ensure relationship is loaded
                .filter(User.id == id)
                .first()
            )
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User no found",
                )

            user_info = UserInfo.from_orm(user)
            if user.attendant_data:
                user_info.attendant_data = AttendantResponse.from_orm(
                    user.attendant_data
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"User with ID {id} is not an attendant",
                )

            return user_info
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving user with attendant data: {str(e)}",
            )
