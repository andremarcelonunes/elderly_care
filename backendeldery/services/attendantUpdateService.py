from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backendeldery import User
from backendeldery.crud import CRUDBase
from backendeldery.models import Attendant
from backendeldery.schemas import UserUpdate, AttendantUpdate


class AttendantUpdateService:
    def __init__(self, db: AsyncSession, updated_by: int, user_ip: str):
        self.db = db
        self.updated_by = updated_by
        self.user_ip = user_ip

    async def update_user(
        self, user_id: int, update_data: UserUpdate, crud_user: CRUDBase
    ) -> User:
        user_update = UserUpdate(**update_data.model_dump(exclude_unset=True))
        return await crud_user.update(
            self.db, user_id, user_update, self.updated_by, self.user_ip
        )

    async def get_attendant(self, user_id: int) -> Attendant:
        result = await self.db.execute(
            select(Attendant).where(Attendant.user_id == user_id)
        )
        attendant = result.scalars().first()
        if not attendant:
            raise HTTPException(status_code=404, detail="Attendant not found")
        return attendant

    def update_attendant_core_fields(
        self, attendant: Attendant, update_data: AttendantUpdate
    ) -> None:
        update_fields = update_data.model_dump(
            exclude={"specialties", "team_names", "function_names"}, exclude_unset=True
        )
        for key, value in update_fields.items():
            setattr(attendant, key, value)
        attendant.updated_by = self.updated_by
        attendant.user_ip = self.user_ip
