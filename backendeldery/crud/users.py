from sqlalchemy.orm import Session
from fastapi import HTTPException
from utils import hash_password, obj_to_dict
from .base import CRUDBase
from models import User, Client, ClientContact, Attendant
from schemas import UserCreate, ClientCreate, ContactCreate, AttendantCreate
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
        # Filtrar apenas os atributos do modelo User
        logger.info("Iniciando criação do user...")
        user_data = {key: value for key, value in obj_in.items() if key in User.__table__.columns.keys()}

        # Hasheia a senha do usuário
        user_data["user_password_hash"] = hash_password(obj_in.pop("user_password"))
        # Adiciona informações de auditoria
        user_data["created_by"] = created_by
        user_data["user_ip"] = user_ip

        # Verifica duplicidade de e-mail e telefone
        if db.query(User).filter(User.user_email == obj_in["user_email"]).first():
            logger.info("email duplicado...")
            raise HTTPException(status_code=400, detail="Email already exists")
        if db.query(User).filter(User.user_phone == obj_in["user_phone"]).first():
            logger.info("telefone  duplicado...")
            raise HTTPException(status_code=400, detail="Phone already exists")

        # Cria a instância do modelo e adiciona ao banco
        db_obj = self.model(**user_data)
        db.add(db_obj)
        db.flush()  # Usa `flush` ao invés de `commit` para preparar a transação sem encerrar
        db.refresh(db_obj)

        return db_obj

class CRUDClient(CRUDBase):
    def __init__(self):
        super().__init__(Client)

    def create(self, db: Session, user: User, obj_in: ClientCreate, created_by: int, user_ip: str):
        """
        Cria um cliente e registra informações de auditoria.
        """
        # Verifica se o usuário já é um cliente
        existing_client = db.query(Client).filter(Client.user_id == user.user_id).first()
        if existing_client:
            raise HTTPException(status_code=400, detail="Client already exists")

        # Converte obj_in para um dicionário e adiciona o user_id
        client_data = obj_in.dict()
        client_data["user_id"] = user.user_id
        client_data["created_by"] = created_by  # Adiciona o campo `created_by`
        client_data["user_ip"] = user_ip

        # Cria a instância do modelo e adiciona ao banco
        obj = self.model(**client_data)
        db.add(obj)
        db.flush()  # Usa `flush` ao invés de `commit` para preparar a transação sem encerrar
        db.refresh(obj)
        return obj


class CRUDContact(CRUDBase):
    def __init__(self):
        super().__init__(ClientContact)

    def create(self, db: Session, client_id: int, user_id: int):
        obj = self.model(user_client_id=client_id, user_contact_id=user_id)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


class CRUDAttendant(CRUDBase):
    def __init__(self):
        super().__init__(Attendant)

    def create(self, db: Session, user: User, obj_in: AttendantCreate, created_by: int, user_ip: str):
        obj_in.user_id = user.user_id
        obj = self.model(**obj_in.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


class CRUDSpecializedUser:
    def __init__(self):
        self.crud_user = CRUDUser()
        self.crud_client = CRUDClient()
        self.crud_contact = CRUDContact()
        self.crud_attendant = CRUDAttendant()

    def create_client(self, db: Session, user_data: dict, created_by: int, user_ip: str):
        """
        Cria um cliente e associa os dados do usuário em uma única transação.
        """
        try:
            if not isinstance(user_data, dict):
                raise ValueError("user_data deve ser um dicionário válido")

            with db.begin():  # Contexto transacional seguro
                # Criação do usuário
                user = self.crud_user.create(
                    db=db,
                    obj_in=user_data,
                    created_by=created_by,
                    user_ip=user_ip
                )
                # Extração de client_data
                client_data = user_data.get("client_data")
                if not client_data:
                    raise HTTPException(status_code=400, detail="client_data é obrigatório para registro de cliente.")

                # Criação do cliente
                client = self.crud_client.create(
                    db=db,
                    user=user,
                    created_by=created_by,
                    user_ip=user_ip,
                    obj_in=ClientCreate(**client_data)
                )
            return {
                "user": obj_to_dict(user),  # Converte User para dicionário
                "client": obj_to_dict(client)  # Converte Client para dicionário
            }

        except HTTPException as e:
            # Repassa a HTTPException diretamente
            raise e
        except Exception as e:
            # Levanta erro genérico apenas para exceções não tratadas
            raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

    def create_contact(self, db: Session, user_data: UserCreate, client_ids: list[int]):
        """
        Cria um contato, registrando o usuário associado e as relações com os clientes.
        """
        user = self.crud_user.create_user(db, obj_in=user_data, created_by=None, user_ip=None)

        for client_id in client_ids:
            self.crud_contact.create(db=db, client_id=client_id, user_id=user.user_id)

        return {"user": user, "clients": client_ids}

    def create_attendant(self, db: Session, user_data: UserCreate, attendant_data: AttendantCreate, created_by: int, user_ip: str):
        user = self.crud_user.create_user(db, obj_in=user_data, created_by=created_by, user_ip=user_ip)
        attendant = self.crud_attendant.create(db, user=user, obj_in=attendant_data, created_by=created_by, user_ip=user_ip)
        return {"user": user, "attendant": attendant}


crud_specialized_user = CRUDSpecializedUser()
crud_user = CRUDUser()
crud_client = CRUDClient()
crud_contact = CRUDContact()
crud_attendant = CRUDAttendant()
