import logging
from typing import Union

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backendeldery import User, CRUDUser
from backendeldery.models import Attendant
from backendeldery.schemas import UserUpdate, AttendantUpdate

logger = logging.getLogger("backendeldery")  # pragma: no cover
logger.setLevel(logging.INFO)  # pragma: no cover
if not logger.hasHandlers():  # pragma: no cover
    console_handler = logging.StreamHandler()  # pragma: no cover
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )  # pragma: no cover
    logger.addHandler(console_handler)  # pragma: no cover


class AttendantUpdateService:
    def __init__(self, db: AsyncSession, updated_by: int, user_ip: str):
        self.db = db
        self.updated_by = updated_by
        self.user_ip = user_ip

    async def update_user(
        self, user_id: int, update_data: UserUpdate, updated_by: int, user_ip: str
    ) -> User:
        # Create a new CRUDUser instance (or use a global one)
        crud_user_instance = CRUDUser()
        # Now call the update method directly with the necessary parameters.
        return await crud_user_instance.update(
            self.db, user_id, update_data, updated_by, user_ip
        )

    async def get_attendant(self, user_id: int) -> Attendant:
        result = await self.db.execute(
            select(Attendant).where(Attendant.user_id == user_id)
        )
        attendant = result.scalars().first()
        if not attendant:
            raise HTTPException(status_code=404, detail="Attendant not found")
        return attendant

    async def update_attendant_core_fields(
        self, attendant: Attendant, update_data: Union[AttendantUpdate, dict]
    ) -> None:
        # Determine update_fields: if update_data is a dict, use it directly; otherwise, use model_dump
        if isinstance(update_data, dict):
            update_fields = update_data
        else:
            update_fields = update_data.model_dump(
                exclude={"specialties", "team_names", "function_names"},
                exclude_unset=True,
            )

        # Also explicitly skip relationship fields if they appear in the dict
        relationship_fields = {"specialties", "team_names", "function_names"}

        for key, value in update_fields.items():
            if key in relationship_fields:
                continue  # Skip these because they're handled separately.
            try:
                logger.info("Setting attribute %s to %s", key, value)
                setattr(attendant, key, value)
            except Exception as ex:
                logger.error("Error setting attribute %s: %s", key, ex)
                raise

        attendant.updated_by = self.updated_by
        attendant.user_ip = self.user_ip
