from sqlalchemy.orm import Session
from crud.users import crud_specialized_user
from schemas import UserCreate, AttendantCreate
from fastapi import HTTPException



    @staticmethod
    async def register_contact(db: Session, user_data: UserCreate):
        """
        Registra um contato no sistema.
        """
        try:
            return crud_specialized_user.create_contact(
                db=db,
                user_data=user_data.dict(),
                client_ids=user_data.client_ids,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail="Erro ao registrar contato.")

    @staticmethod
    async def register_attendant(
        db: Session, user_data: UserCreate, attendant_data: AttendantCreate, created_by: int, user_ip: str
    ):
        """
        Registra um atendente no sistema.
        """
        try:
            return crud_specialized_user.create_attendant(
                db=db,
                user_data=user_data.dict(),
                attendant_data=attendant_data.dict(),
                created_by=created_by,
                user_ip=user_ip,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail="Erro ao registrar atendente.")