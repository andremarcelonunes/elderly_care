import logging
import traceback
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload, selectinload

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
    UserUpdate,
)
from backendeldery.services.attendantAssociationService import (
    AttendantAssociationService,
)
from backendeldery.services.attendantUpdateService import (
    AttendantUpdateService,
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

            user_info = UserInfo.model_validate(user)
            if user.attendant_data:
                user_info.attendant_data = AttendantResponse.model_validate(
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

    async def get_async(self, db: AsyncSession, id: int) -> dict:
        """
        Fetches a user (with attendant data) by ID using AsyncSession and returns
        a fully validated UserInfo model dumped to a plain dictionary.
        """
        user = None  # Initialize user
        try:
            try:
                result = await db.execute(
                    select(self.model)
                    .options(
                        selectinload(self.model.attendant_data)
                        .selectinload(Attendant.specialty_associations)
                        .selectinload(AttendantSpecialty.specialty),
                        selectinload(self.model.attendant_data)
                        .selectinload(Attendant.team_associations)
                        .selectinload(AttendantTeam.team),
                        selectinload(self.model.attendant_data).selectinload(
                            Attendant.function
                        ),
                    )
                    .filter(self.model.id == id)
                )
                user = result.scalar_one_or_none()
            except Exception as e:
                logger.error("Error in get_user: %s", traceback.format_exc())
                if user:
                    logger.error("attendant_data: %s", user.attendant_data)
                    logger.error(
                        "specialty_names: %s",
                        getattr(user.attendant_data, "specialty_names", None),
                    )
                raise

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Build a dictionary of the user's data.
            user_data = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "active": user.active,
                # Override client_data to avoid lazy-loading issues.
                "client_data": None,
                # We'll replace attendant_data below.
                "attendant_data": None,
            }

            # Convert the nested attendant_data to a dictionary.
            if user.attendant_data:
                attendant_model = AttendantResponse.model_validate(user.attendant_data)
                user_data["attendant_data"] = (
                    attendant_model.dict()
                )  # Ensure it's a dict.
            else:
                raise HTTPException(
                    status_code=404, detail=f"User with ID {id} is not an attendant"
                )

            # Validate and create the main Pydantic model.
            user_info = UserInfo.model_validate(user_data)
            # Dump the final model into a plain dictionary before returning.
            return user_info.model_dump()  # or user_info.dict() if using Pydantic v1

        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving user with attendant data: {str(e)}",
            )

    async def update(
        self,
        db: AsyncSession,
        user_id: int,
        update_data: UserUpdate,
        updated_by: int,
        user_ip: str,
    ) -> Attendant:
        try:
            update_dict = update_data.model_dump(exclude_unset=True)
            attendant_data = update_dict.pop("attendant_data", None)

            update_service = AttendantUpdateService(db, updated_by, user_ip)
            try:
                user = await update_service.update_user(
                    user_id, update_data, updated_by, user_ip
                )
            except Exception as e:
                logger.error("Error in update_user: %s", traceback.format_exc())
                raise
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            try:
                attendant = await update_service.get_attendant(user_id)
            except Exception as e:
                logger.error("Error in update_user: %s", traceback.format_exc())
                raise

            if attendant is None:
                raise HTTPException(status_code=404, detail="Attendant not found")

            if attendant_data:
                try:
                    await update_service.update_attendant_core_fields(
                        attendant, attendant_data
                    )
                except Exception as e:
                    logger.error("Error in update_user: %s", traceback.format_exc())
                    raise
            try:
                association_service = AttendantAssociationService(
                    db, attendant.user_id, updated_by, user_ip
                )
            except Exception as e:
                logger.error("Error in update_user: %s", traceback.format_exc())
                raise
            if attendant_data:
                if attendant_data.get("team_names"):
                    try:
                        await association_service.update_team_associations(
                            attendant_data.get("team_names"), self.crud_team
                        )
                        logger.info(
                            "NOmes dos times passados a update_team_association: %s",
                            attendant_data.get("team_names"),
                        )
                    except Exception as e:
                        logger.error("Error in update_user: %s", traceback.format_exc())
                        raise
                if attendant_data.get("function_names"):
                    try:
                        attendant.function = (
                            await association_service.update_function_association(
                                attendant_data.get("function_names"), self.crud_function
                            )
                        )
                    except Exception as e:
                        logger.error("Error in update_user: %s", traceback.format_exc())
                        raise
                if attendant_data.get("specialties"):
                    try:
                        await association_service.update_specialty_associations(
                            attendant_data.get("specialties")
                        )
                    except Exception as e:
                        logger.error("Error in update_user: %s", traceback.format_exc())
                        raise

            await db.commit()  # Explicitly commit the changes
            await db.refresh(attendant)
            return attendant

        except HTTPException as e:
            raise e
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to update attendant: {str(e)}"
            ) from e
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
