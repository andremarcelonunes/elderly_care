from sqlalchemy.orm import Session
from fastapi import HTTPException
from utils import hash_password
from crud.crud_base import CRUDBase
from models import User
from schemas import UserCreate, UserResponse


class CRUDUser(CRUDBase[User, UserCreate]):
    def __init__(self):
        super().__init__(User)

    def create(self, db: Session, obj_in: UserCreate, created_by: int, user_ip: str) -> UserResponse:
        """
        Cria um novo usuário e registra informações de auditoria.
        """
        # Converte os dados recebidos em um dicionário
        user_data = obj_in.dict()
        # Hasheia a senha do usuário
        user_data["user_password_hash"] = hash_password(user_data.pop("user_password"))
        # Adiciona informações de auditoria
        user_data["created_by"] = created_by
        user_data["user_ip"] = user_ip

        # Verifica duplicidade de e-mail e telefone
        if db.query(User).filter(User.user_email == obj_in.user_email).first():
            raise HTTPException(status_code=400, detail="Email already exists")
        if db.query(User).filter(User.user_phone == obj_in.user_phone).first():
            raise HTTPException(status_code=400, detail="Phone already exists")

        # Cria a instância do modelo e adiciona ao banco
        db_obj = self.model(**user_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Retorna o objeto formatado como UserResponse
        return UserResponse.from_orm(db_obj)


# Instância do CRUDUser
crud_user = CRUDUser()