from sqlalchemy.orm import Session, joinedload
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy import update
from fastapi import HTTPException
from backendeldery.utils import hash_password, obj_to_dict
from backendeldery.models import User, Client
from backendeldery.schemas import UserCreate, SubscriberCreate, UserInfo, SubscriberInfo, UserUpdate
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
        client_data = obj_in.model_dump()
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

    def search_subscriber(self, db: Session, criteria: dict):
        """
        Busca um assinante com base nos critérios fornecidos.
        """
        try:
            field, value = next(iter(criteria.items()))

            if field == "cpf":
                # Query Client table via CPF
                return (
                    db.query(self.crud_user.model)
                    .join(self.crud_client.model)
                    .filter(self.crud_client.model.cpf == value)
                    .first()
                )
            elif field in ["email", "phone"]:
                # Query User table directly
                return (
                    db.query(self.crud_user.model)
                    .filter(getattr(self.crud_user.model, field) == value)
                    .first()
                )
            else:
                return None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error to search subscriber: {str(e)}")

    def get_user_with_client(self, db: Session, user_id: int):
        """
        Retrieve a user along with their client data by user ID.
        """
        try:
            user = (
                db.query(self.crud_user.model)
                .outerjoin(self.crud_client.model, self.crud_user.model.id == self.crud_client.model.user_id)
                .filter(self.crud_user.model.id == user_id)
                .first()
            )
            if not user:
                return None

            user_info = UserInfo.from_orm(user)
            if user.client:
                user_info.client_data = SubscriberInfo.from_orm(user.client)
                return user_info
            return None
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user with client data: {str(e)}")

    @staticmethod
    async def update_user_and_client(
            db_session: Session,
            user_id: int,
            user_update: UserUpdate,
            user_ip: str,
            updated_by: int
    ):
        try:
            # Fetch the user and client in a single query
            result = db_session.execute(
                select(User).options(joinedload(User.client)).where(User.id == user_id)
            )
            user = result.scalars().one_or_none()

            if not user:
                db_session.rollback()
                return {"error": "User not found"}

            # Convert the data to a dictionary and exclude unset values
            user_data = {k: v for k, v in user_update.dict(exclude_unset=True).items() if v is not None}
            client_data = user_data.pop("client_data", None)

            # Variables to track if there were changes
            user_updated = False
            client_updated = False

            # Update user fields dynamically
            if user_data:
                user_data["user_ip"] = user_ip
                user_data["updated_by"] = updated_by
                db_session.execute(
                    update(User).where(User.id == user_id).values(**user_data)
                )
                user_updated = True

            # Update client fields dynamically (if there is data and the client exists)
            if client_data and user.client:
                client_data["user_ip"] = user_ip
                client_data["updated_by"] = updated_by
                db_session.execute(
                    update(Client).where(Client.user_id == user_id).values(**client_data)
                )
                client_updated = True

            # Commit asynchronously if there were changes
            if user_updated or client_updated:
                db_session.commit()
                return {"message": "User and Client are updated!"}

            return {"message": "Nothing to update."}

        except NoResultFound:
            db_session.rollback()
            return {"error": "User not found."}
        except Exception as e:
            db_session.rollback()
            return {"error": f"Error to update: {str(e)}"}


crud_specialized_user = CRUDSpecializedUser()
crud_user = CRUDUser()
crud_client = CRUDClient()
