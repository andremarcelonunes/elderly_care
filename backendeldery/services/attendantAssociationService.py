import logging
import traceback
from typing import Optional, List, Set, Dict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backendeldery.crud.function import CRUDFunction
from backendeldery.crud.team import CRUDTeam
from backendeldery.models import (
    AttendantTeam,
    Team,
    Function,
    AttendantSpecialty,
    Specialty,
)

logger = logging.getLogger("backendeldery")  # pragma: no cover
logger.setLevel(logging.INFO)  # pragma: no cover
if not logger.hasHandlers():  # pragma: no cover
    console_handler = logging.StreamHandler()  # pragma: no cover
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )  # pragma: no cover
    logger.addHandler(console_handler)  # pragma: no cover


class AttendantAssociationService:
    def __init__(self, db: AsyncSession, user_id: int, updated_by: int, user_ip: str):
        self.db = db
        self.user_id = user_id
        self.updated_by = updated_by
        self.user_ip = user_ip

    async def update_team_associations(
        self, team_names: Optional[List[str]], crud_team: CRUDTeam
    ) -> None:
        if not team_names:
            return
        existing_team_ids = await self._get_existing_team_ids()
        team_map = await self._get_or_create_teams(team_names, crud_team)
        await self._create_new_team_associations(team_map, existing_team_ids)

    async def _get_existing_team_ids(self) -> Set[int]:
        result = await self.db.execute(
            select(AttendantTeam.team_id).where(
                AttendantTeam.attendant_id == self.user_id
            )
        )
        return set(result.scalars().all())

    async def _get_or_create_teams(
        self, team_names: List[str], crud_team: CRUDTeam
    ) -> Dict[str, Team]:
        unique_names = set(team_names)
        teams = {}
        for name in unique_names:
            team = await crud_team.get_by_name_async(self.db, name)
            if not team:
                team = await crud_team.create_async(
                    self.db, name, "default", self.updated_by, self.user_ip
                )

            teams[name] = team
        return teams

    async def _create_new_team_associations(
        self, team_map: Dict[str, Team], existing_team_ids: Set[int]
    ) -> None:
        new_associations = [
            AttendantTeam(
                attendant_id=self.user_id,
                team_id=team.team_id,
                created_by=self.updated_by,
                user_ip=self.user_ip,
            )
            for team in team_map.values()
            if team.team_id not in existing_team_ids
        ]
        if new_associations:
            self.db.add_all(new_associations)

    async def update_function_association(
        self, function_name: Optional[str], crud_function: CRUDFunction
    ):
        if not function_name:
            return None
        logger.info("o nome da função é %s", function_name)
        result = await self.db.execute(
            select(Function).where(Function.name == function_name)
        )
        function = result.scalars().first()
        if not function:
            function = await crud_function.create(
                self.db,
                function_name,
                "Auto-created function",
                self.updated_by,
                self.user_ip,
            )
        return function

    async def update_specialty_associations(
        self, specialties: Optional[List[str]]
    ) -> None:
        if not specialties:
            return
        existing_ids = await self._get_existing_specialty_ids()
        specialty_map = await self._get_or_create_specialties(specialties)
        await self._create_specialty_associations(
            specialties, specialty_map, existing_ids
        )

    async def _get_existing_specialty_ids(self) -> Set[int]:
        result = await self.db.execute(
            select(AttendantSpecialty.specialty_id).where(
                AttendantSpecialty.attendant_id == self.user_id
            )
        )
        return set(result.scalars().all())

    async def _get_or_create_specialties(
        self, names: List[str]
    ) -> Dict[str, Specialty]:
        unique_names = set(names)
        result = await self.db.execute(
            select(Specialty).where(Specialty.name.in_(unique_names))
        )
        existing = {s.name: s for s in result.scalars().all()}
        new_specialties = {}
        for name in unique_names - existing.keys():
            spec = Specialty(
                name=name, created_by=self.updated_by, user_ip=self.user_ip
            )
            self.db.add(spec)
            await self.db.flush()
            new_specialties[name] = spec
        return {**existing, **new_specialties}

    async def _create_specialty_associations(
        self,
        specialties: List[str],
        specialty_map: Dict[str, Specialty],
        existing_ids: Set[int],
    ) -> None:
        new_associations = [
            AttendantSpecialty(
                attendant_id=self.user_id,
                specialty_id=specialty_map[name].id,
                created_by=self.updated_by,
                user_ip=self.user_ip,
            )
            for name in specialties
            if specialty_map[name].id not in existing_ids
        ]
        if new_associations:
            self.db.add_all(new_associations)

    async def delete_team_relation(
        self,
        db: AsyncSession,
        attendant_id: int,
        team_id: int,
    ) -> dict:
        """
        Delete the association between an attendant and a team.

        Args:
            db: Database session
            attendant_id: ID of the attendant
            team_id: ID of the team

        Returns:
            Dictionary with status message
        """
        try:
            # First update the association with audit information
            result = await db.execute(
                select(AttendantTeam).where(
                    AttendantTeam.attendant_id == attendant_id,
                    AttendantTeam.team_id == team_id,
                )
            )
            association = result.scalars().first()

            if not association:
                raise HTTPException(
                    status_code=404, detail="Team association not found"
                )

            # Update with audit information
            association.updated_by = self.updated_by
            association.user_ip = self.user_ip

            # Hard delete the association
            await db.delete(association)
            await db.commit()

            return {
                "status": "success",
                "message": f"Team association between attendant {attendant_id} and team {team_id} deleted successfully",
            }

        except HTTPException as e:
            await db.rollback()
            raise e
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting team association: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"Failed to delete team association: {str(e)}"
            )
