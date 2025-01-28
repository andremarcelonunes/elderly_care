from sqlalchemy.orm import Session
from backendeldery.crud.users import crud_specialized_user
from backendeldery.schemas import UserCreate
from backendeldery.validators.user_validator import UserValidator
from fastapi import HTTPException


class UserService:
    @staticmethod
    async def register_client(db: Session, user_data: UserCreate, created_by: int, user_ip: str):
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
