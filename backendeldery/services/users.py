from sqlalchemy.orm import Session
from backendeldery.crud.users import crud_specialized_user, crud_assisted
from backendeldery.schemas import UserCreate, UserUpdate, UserResponse
from backendeldery.validators.user_validator import UserValidator
from fastapi import HTTPException


class UserService:
    @staticmethod
    async def register_client(
            db: Session, user_data: UserCreate, created_by: int, user_ip: str
    ):
        """
        Registra um cliente no sistema.
        """
        try:
            UserValidator.validate_subscriber(db, user_data.model_dump())
            return crud_specialized_user.create_subscriber(
                db=db,
                user_data=user_data.model_dump(),  # Use model_dump instead of dict
                created_by=created_by,
                user_ip=user_ip,
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

    @staticmethod
    async def search_subscriber(db: Session, criteria: dict):
        try:
            user = crud_specialized_user.search_subscriber(db, criteria)
            if user:
                return user.id  # Return only the user ID
            return None
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error in UserService: {str(e)}"
            )

    @staticmethod
    async def get_subscriber_by_id(db: Session, user_id: int):
        """
        Get subscriber information by user ID.
        """
        try:
            user = crud_specialized_user.get_user_with_client(db=db, user_id=user_id)
            if user:
                return user
            return None
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error in UserService: {str(e)}"
            )

    @staticmethod
    async def update_subscriber(
            db: Session,
            user_id: int,
            user_update: UserUpdate,
            user_ip: str,
            updated_by: int,
    ):
        """
        Serviço que chama o CRUD para atualizar um usuário e seu cliente.
        """
        try:
            # Chama o CRUD para fazer a atualização real no banco
            UserValidator.validate_user(db, user_update)
            result = await crud_specialized_user.update_user_and_client(
                db, user_id, user_update, user_ip, updated_by
            )
            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])

            # Fetch the updated user to return the correct response
            updated_user = crud_specialized_user.get_user_with_client(db, user_id)
            if not updated_user:
                raise HTTPException(status_code=404, detail="User not found")

            return UserResponse(
                id=updated_user.id,
                name=updated_user.name,
                email=updated_user.email,
                phone=updated_user.phone,
                role=updated_user.role,
                active=updated_user.active,
                client_data=updated_user.client_data.dict(),  # Convert to dictionary
            )

        except HTTPException as e:
            raise e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error on updating: {str(e)}")

    @staticmethod
    async def create_association_assisted(
            db: Session,
            subscriber_id: int,
            assisted_id: int,
            user_ip: str,
            created_by: int,
    ):
        """
        Creates an association in the client_association table and registers a new
        client if the assisted is not the same as the subscriber.
        """
        try:
            # Validate the assisted data
            UserValidator.validate_association_assisted(db, subscriber_id, assisted_id)

            # Create the association
            return crud_assisted.create_association(
                db, subscriber_id, assisted_id, created_by, user_ip
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
