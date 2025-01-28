from sqlalchemy.orm import Session
from fastapi import HTTPException
from backendeldery.utils import hash_password, obj_to_dict
from backendeldery.models import User, Client
from backendeldery.schemas import UserCreate, SubscriberCreate
from .base import CRUDBase
import logging


logger = logging.getLogger("backendeldery")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(console_handler)

class CRUDUser(CRUDBase[User, UserCreate]):
    def __init__(self):
        super().__init__(User)

    def create(self, db: Session, obj_in: dict, created_by: int, user_ip: str) -> User:
        """
        Cria um novo usuário e registra informações de auditoria.
        """
        logger.info("Iniciando criação do user...")
        user_data = {key: value for key, value in obj_in.items() if key in User.__table__.columns.keys()}
        user_data["password_hash"] = hash_password(obj_in.pop("password"))
        user_data["created_by"] = created_by
        user_data["user_ip"] = user_ip
        db_obj = self.model(**user_data)
        db.add(db_obj)
        db.flush()  # Usa `flush` ao invés de `commit` para preparar a transação sem encerrar
        db.refresh(db_obj)
        return db_obj

class CRUDClient(CRUDBase):
    def __init__(self):
        super().__init__(Client)

    def create(self, db: Session, user: User, obj_in: SubscriberCreate, created_by: int, user_ip: str):
        """
        Cria um cliente e registra informações de auditoria.
        """
        client_data = obj_in.model_dump()   # Converte para dicionário
        client_data["user_id"] = user.id
        client_data["created_by"] = created_by
        client_data["user_ip"] = user_ip
        obj = self.model(**client_data)
        db.add(obj)
        db.flush()  # Usa `flush` para preparar a transação sem encerrar
        db.refresh(obj)
        return obj


class CRUDSpecializedUser:
    def __init__(self):
        self.crud_user = CRUDUser()
        self.crud_client = CRUDClient()

    def create_subscriber(self, db: Session, user_data: dict, created_by: int, user_ip: str):
        """
        Cria um assinante e associa os dados do usuário em uma única transação.
        """
        try:
            user = self.crud_user.create(
                db=db,
                obj_in=user_data,
                created_by=created_by,
                user_ip=user_ip
            )

            client = self.crud_client.create(
                db=db,
                user=user,
                created_by=created_by,
                user_ip=user_ip,
                obj_in=SubscriberCreate(**user_data["client_data"])
            )

            db.commit()  # Commit the transaction

            return {
                "user": obj_to_dict(user),  # Converte User para dicionário
                "client": obj_to_dict(client)  # Converte Client para dicionário
            }
        except Exception as e:
            db.rollback()  # Rollback the transaction in case of error
            raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")
        finally:
            db.close()  # Ensure the session is closed


crud_specialized_user = CRUDSpecializedUser()
crud_user = CRUDUser()
crud_client = CRUDClient()
