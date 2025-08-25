from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backendeldery.crud.attendant import CRUDAttendant
from backendeldery.crud.team import CRUDTeam
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
            return CRUDAttendant().get(db, id)
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
            await UserValidator.validate_user_async(db, user_update)
            await CRUDAttendant().update(db, user_id, user_update, updated_by, user_ip)
            updated_attendant = await CRUDAttendant().get_async(db, user_id)
            if not updated_attendant:
                raise HTTPException(status_code=404, detail="Attendant not found")
            return updated_attendant  # Already in final form.
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error on updating: {str(e)}")

    @staticmethod
    async def list_attendants_by_team(
        db: AsyncSession,
        team_id: int,
    ):
        """
        Retrieve all attendants associated with a specific team.

        Args:
            db: Database session
            team_id: ID of the team

        Returns:
            List of attendants associated with the team
        """
        try:

            # Create a new instance of CRUDTeam
            crud_team = CRUDTeam()

            # Call the method with proper await
            attendants = await crud_team.list_attendants(db=db, team_id=team_id)
            return attendants

        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to retrieve team attendants: {str(e)}"
            )

    @staticmethod
    async def get_clients_for_attendant(db: AsyncSession, attendant_id: int):
        """
        Retrieve all clients for the teams that the attendant is associated with.
        Returns a list of dictionaries ready to be parsed into UserResponse.
        """
        from sqlalchemy.inspection import inspect

        def orm_to_dict(obj):
            return {
                c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs
            }

        crud_team = CRUDTeam()
        teams = await crud_team.get_teams_by_attendant_id(db, attendant_id)
        if not teams:
            raise HTTPException(
                status_code=404, detail="Attendant not associated to any team"
            )

        clients = []
        for team in teams:
            if hasattr(team, "clients") and team.clients:
                clients.extend(team.clients)
        # Remove duplicate clients by user_id if needed
        unique_clients = {client.user_id: client for client in clients}.values()

        result = []
        for client in unique_clients:
            # Now that the 'user' relationship is eagerly loaded, this won't trigger a lazy load.
            user_dict = orm_to_dict(client.user) if client.user else {}
            client_dict = orm_to_dict(client)
            merged = {
                **user_dict,
                "client_data": client_dict,
                "attendant_data": None,  # set to None or fill as needed
            }
            result.append(merged)
        return result

    @staticmethod
    async def search_attendant(db, criteria):
        try:
            crud_attendant = CRUDAttendant()
            user = await crud_attendant.search_attendant(db, criteria)
            if user:
                return user.id  # Return only the user ID
            return None
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error in AttendantService: {str(e)}"
            )
