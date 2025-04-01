import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload

from backendeldery.models import (
    Client,
    User,
    client_association,
    client_contact_association,
)
from backendeldery.schemas import (
    SubscriberCreate,
    SubscriberInfo,
    UserCreate,
    UserInfo,
    UserUpdate,
)
from backendeldery.utils import hash_password, obj_to_dict

from .base import CRUDBase

logger = logging.getLogger("backendeldery")  # pragma: no cover
logger.setLevel(logging.CRITICAL)  # pragma: no cover
if not logger.hasHandlers():  # pragma: no cover
    console_handler = logging.StreamHandler()  # pragma: no cover
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )  # pragma: no cover
    logger.addHandler(console_handler)  # pragma: no cover


class CRUDUser(CRUDBase[User, UserCreate]):
    def __init__(self):
        super().__init__(User)

    async def create(
        self, db: Session, obj_in: dict, created_by: int, user_ip: str
    ) -> User:
        """
        Cria um novo usuário e registra informações de auditoria.
        """
        logger.info("Iniciando criação do user...")
        user_data = {
            key: value
            for key, value in obj_in.items()
            if key in User.__table__.columns.keys()
        }
        user_data["password_hash"] = hash_password(obj_in.pop("password"))
        user_data["created_by"] = created_by
        user_data["user_ip"] = user_ip
        db_obj = crud_user.model(**user_data)
        db.add(db_obj)
        db.flush()  # Usa `flush` ao invés de `commit` para preparar a transação sem encerrar
        db.refresh(db_obj)
        return db_obj

    async def get(self, db: Session, id: int) -> Optional[dict]:
        """Fetches a user and attaches related data
        (client or attendant) dynamically."""
        user = db.query(self.model).filter(self.model.id == id).first()
        if user:
            data = obj_to_dict(user)
            # Attach client_data or attendant_data based on role
            if user.role == "attendant":
                data["attendant_data"] = (
                    obj_to_dict(user.attendant_data) if user.attendant_data else None
                )
            elif user.role == "client":
                data["client_data"] = (
                    obj_to_dict(user.client_data) if user.client_data else None
                )
            return data
        raise HTTPException(
            status_code=404,
            detail="User no found",
        )

    async def update(
        self,
        db: AsyncSession,
        user_id: int,
        update_data: UserUpdate,
        updated_by: int,
        user_ip: str,
    ) -> User:

        # Ensure update_data is a Pydantic model.
        if not hasattr(update_data, "model_dump"):
            update_data = UserUpdate(**update_data)

        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Determine allowed fields (columns) to update.
        allowed_fields = set(User.__table__.columns.keys())
        # Exclude relationship fields like "attendant_data" or "client_data"
        user_data = {
            k: v
            for k, v in update_data.model_dump(exclude_unset=True).items()
            if v is not None and k in allowed_fields
        }

        # Apply the filtered updates
        for key, value in user_data.items():
            setattr(user, key, value)

        # Update audit fields
        user.updated_by = updated_by
        user.user_ip = user_ip

        db.add(user)
        return user


class CRUDClient(CRUDBase):
    def __init__(self):
        super().__init__(Client)

    async def create(
        self,
        db: Session,
        user: User,
        obj_in: SubscriberCreate,
        created_by: int,
        user_ip: str,
    ):
        """
        Cria um cliente e registra informações de auditoria.
        """
        client_data = obj_in.model_dump()
        client_data["user_id"] = user.id
        client_data["created_by"] = created_by
        client_data["user_ip"] = user_ip
        obj = crud_client.model(**client_data)
        db.add(obj)
        db.flush()  # Usa `flush` para preparar a transação sem encerrar
        db.refresh(obj)
        return obj


class CRUDSpecializedUser:
    def __init__(self):
        self.crud_user = CRUDUser()
        self.crud_client = CRUDClient()

    async def create_subscriber(
        self, db: Session, user_data: dict, created_by: int, user_ip: str
    ):
        """
        Cria um assinante e associa os dados do usuário em uma única transação.
        """
        try:
            user = await crud_user.create(
                db=db, obj_in=user_data, created_by=created_by, user_ip=user_ip
            )

            await crud_client.create(
                db=db,
                user=user,
                created_by=created_by,
                user_ip=user_ip,
                obj_in=SubscriberCreate(**user_data["client_data"]),
            )

            db.commit()  # Commit the transaction

            if not user:
                return None
            user_info = UserInfo.from_orm(user)
            if user.client:
                user_info.client_data = SubscriberInfo.from_orm(user.client)
                return user_info
            return None

        except Exception as e:
            db.rollback()  # Rollback the transaction in case of error
            raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")
        finally:
            db.close()  # Ensure the session is closed

    async def search_subscriber(self, db: Session, criteria: dict):
        """
        Busca um assinante com base nos critérios fornecidos.
        """
        try:
            field, value = next(iter(criteria.items()))

            if field == "cpf":
                # Query Client table via CPF
                return (
                    db.query(crud_user.model)
                    .join(crud_client.model)
                    .filter(crud_client.model.cpf == value)
                    .first()
                )
            elif field in ["email", "phone"]:
                # Query User table directly
                return (
                    db.query(crud_user.model)
                    .filter(getattr(crud_user.model, field) == value)
                    .first()
                )
            else:
                return None
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error to search subscriber: {str(e)}"
            )

    async def get_user_with_client(self, db: Session, user_id: int):
        """
        Retrieve a user along with their client data by user ID.
        """
        try:
            user = (
                db.query(crud_user.model)
                .outerjoin(
                    crud_client.model,
                    crud_user.model.id == crud_client.model.user_id,
                )
                .filter(crud_user.model.id == user_id)
                .first()
            )
            if not user:
                return None

            user_info = UserInfo.from_orm(user)
            if user.client:
                user_info.client_data = SubscriberInfo.from_orm(user.client)

            return user_info
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving user with client data: {str(e)}",
            )

    async def update_user_and_client(
        self,
        db_session: Session,
        user_id: int,
        user_update: UserUpdate,
        user_ip: str,
        updated_by: int,
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
            user_data = {
                k: v
                for k, v in user_update.dict(exclude_unset=True).items()
                if v is not None
            }
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
                    update(Client)
                    .where(Client.user_id == user_id)
                    .values(**client_data)
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


class CRUDAssisted:
    def __init__(self):
        self.model = client_association

    async def create_association(
        self,
        db: Session,
        subscriber_id: int,
        assisted_id: int,
        created_by: int,
        user_ip: str,
    ):
        """
        Creates an association in the client_association table.
        """
        try:
            # Fetch the user to check the role
            user = db.query(User).filter(User.id == subscriber_id).one_or_none()
            if not user:
                raise ValueError("User not found")

            # Create the association
            db.execute(
                crud_assisted.model.insert().values(
                    subscriber_id=subscriber_id,
                    assisted_id=assisted_id,
                    created_by=created_by,
                    user_ip=user_ip,
                )
            )
            db.commit()
            return {"message": "Association created successfully"}

        except ValueError as e:
            db.rollback()
            raise e
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Error creating association: {str(e)}")

    async def get_assisted_clients_by_subscriber(self, db: Session, subscriber_id: int):
        """
        Retrieves the assisted clients for a given subscriber by first querying the User,
        then accessing the assisted_clients property.
        """
        user = db.query(User).filter(User.id == subscriber_id).one_or_none()
        if not user:
            raise ValueError("User not found")
        return user.assisted_clients


class CRUDContact:
    def __init__(self, user_crud: CRUDUser):
        self.user_crud = user_crud
        self.model = client_contact_association

    async def create_contact(
        self,
        db: Session,
        user_data: dict,
        created_by: int,
        user_ip: str,
    ):
        """
        Creates a contact
        """
        try:
            # Fetch the user to check the role
            user = await crud_user.create(
                db=db, obj_in=user_data, created_by=created_by, user_ip=user_ip
            )
            if not user:
                raise ValueError("User not found")

            db.commit()
            return user

        except ValueError as e:
            db.rollback()
            raise e
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Error creating contact: {str(e)}")

    async def create_contact_association(
        self,
        db: Session,
        client_id: int,
        user_contact_id: int,
        created_by: int,
        user_ip: str,
    ):
        """
        Associate a contact  to some client.
        """
        try:
            association = client_contact_association.insert().values(
                user_client_id=client_id,  # The client's user_id
                user_contact_id=user_contact_id,  # The contact's user id
                created_by=created_by,
                updated_by=None,
                user_ip=user_ip,
            )
            db.execute(association)
            db.commit()
            return {"message": "Association created successfully"}

        except ValueError as e:
            db.rollback()
            raise e
        except Exception as e:
            db.rollback()
            raise RuntimeError(
                f"Error creating association between contact and client: {str(e)}"
            )

    async def get_contacts_by_client(self, db: Session, client_id: int):
        """
        Retrieves all contacts for a given client.
        """
        client = db.query(Client).filter(Client.user_id == client_id).one_or_none()
        if not client:
            raise ValueError("Client not found")
        return client.contacts

    async def get_clients_by_contact(self, db: Session, contact_id: int):
        """
        Retrieves all clients associated with the given contact (User)
        from the association table, excluding the contact's own client
        record (if any).
        """

        # Retrieve the user record (contact)
        user = db.query(User).filter(User.id == contact_id).one_or_none()
        if not user:
            raise ValueError("User not found")

        # Get all associated clients through the many-to-many relationship
        associated_clients = list(user.clients)

        # Filter out the user's own client record (if the contact is also a client)
        filtered_clients = [
            client for client in associated_clients if client.user_id != contact_id
        ]

        return filtered_clients

    async def delete_contact_association(
        self, db: Session, client_id: int, contact_id: int
    ):
        """
        Deletes the association record for a given client and contact.
        Returns the number of rows deleted.
        """
        deleted_count = (
            db.query(client_contact_association)
            .filter(
                client_contact_association.c.user_client_id == client_id,
                client_contact_association.c.user_contact_id == contact_id,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted_count

    async def delete_contact_if_orphan(self, db: Session, contact_id: int):
        """
        Checks if the contact is still associated with any client.
        If not, deletes the contact from the User table and returns the deleted contact.
        """
        remaining = (
            db.query(client_contact_association)
            .filter(client_contact_association.c.user_contact_id == contact_id)
            .count()
        )
        if remaining == 0:
            contact = db.query(User).filter(User.id == contact_id).one_or_none()
            if contact:
                db.delete(contact)
                db.commit()
                return contact
        return None

    async def delete_contact_relation(
        self, db: Session, client_id: int, contact_id: int, user_ip: str, x_user_id: int
    ):
        """
        Updates the association with audit data (if needed) and then
        deletes the association between the specified client and contact.
        If the contact is not associated with any other client, deletes
        the contact record too.
        """
        # (Optional) Update the association row with audit info.
        _unused_updated_rows = (
            db.query(client_contact_association)
            .filter(
                client_contact_association.c.user_client_id == client_id,
                client_contact_association.c.user_contact_id == contact_id,
            )
            .update(
                {"updated_by": x_user_id, "user_ip": user_ip}, synchronize_session=False
            )
        )
        db.commit()

        # Delete the association row.
        deleted_count = await crud_contact.delete_contact_association(
            db, client_id, contact_id
        )
        if deleted_count == 0:
            raise ValueError("Association not found")

        # Delete the contact record if it is now orphaned.
        await crud_contact.delete_contact_if_orphan(db, contact_id=contact_id)

        return True


crud_assisted = CRUDAssisted()
crud_specialized_user = CRUDSpecializedUser()
crud_user = CRUDUser()
crud_contact = CRUDContact(user_crud=crud_user)
crud_client = CRUDClient()
