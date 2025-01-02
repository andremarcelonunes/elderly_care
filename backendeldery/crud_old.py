from models import User, Client, Contact, NotificationConfig, Team, Attendant
from passlib.context import CryptContext
from fastapi import HTTPException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def obj_to_dict(obj, exclude_fields=[]):
    if not obj:
        return None
    return {col.name: getattr(obj, col.name) for col in obj.__table__.columns if col.name not in exclude_fields}


class CRUDBase:
    def __init__(self, model):
        self.model = model

    def create(self, db, obj_in):
        obj_data = self.model(**obj_in if isinstance(obj_in, dict) else obj_in.dict())
        self.validate_foreign_keys(db, obj_data)
        db.add(obj_data)
        db.commit()
        db.refresh(obj_data)
        return obj_to_dict(obj_data)

    def create_many(self, db, objs_in):
        responses = []
        for obj_in in objs_in:
            self.validate_foreign_keys(db, obj_in)
            obj = self.model(**obj_in if isinstance(obj_in, dict) else obj_in.dict())
            db.add(obj)
            db.commit()
            db.refresh(obj)
            responses.append(obj_to_dict(obj))
        return responses

    def get(self, db, id):
        obj = db.query(self.model).filter(self.model.id == id).first()
        if not obj:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found")
        return obj_to_dict(obj)

    def validate_foreign_keys(self, db, obj_in):
        for fk in self.model.__table__.foreign_keys:
            column_name = fk.parent.name  # Nome da coluna local
            related_model = fk.column.table  # Tabela relacionada
            related_value = getattr(obj_in, column_name, None)

            # Se o valor for None, não valida a chave estrangeira
            if related_value is not None:
                # Mapeia a tabela para o modelo SQLAlchemy correspondente
                related_model_class = db.registry.mappers[related_model]
                related_obj = db.query(related_model_class).filter(
                    getattr(related_model_class, fk.column.name) == related_value
                ).first()

                if not related_obj:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid foreign key: {related_model.name}.{fk.column.name} with value {related_value} does not exist."
                    )


class CRUDUser(CRUDBase):
    def __init__(self):
        super().__init__(User)

    def create(self, db, obj_in):
        user_data = obj_in.dict()
        user_data["password_hash"] = pwd_context.hash(user_data.pop("password"))
        obj = self.model(**user_data)
        existing_email = db.query(User).filter(User.user_email == obj_in.user_email).first()
        existing_phone = db.query(User).filter(User.user_phone == obj_in.user_phone).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone already exists")
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return {"user_id": obj.user_id}


class CRUDClient(CRUDBase):
    def __init__(self):
        super().__init__(Client)

    def create(self, db, obj_in):
        # Verifica se o usuário já é um cliente
        existing_client = db.query(Client).filter(Client.user_id == obj_in.user_id).first()
        if existing_client:
            raise HTTPException(status_code=400, detail="Client already exists")
        obj = self.model(**obj_in.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj_to_dict(obj)


class CRUDContact(CRUDBase):
    def __init__(self):
        super().__init__(Contact)

    def create_or_update_many(self, db, objs_in):
        responses = []
        for obj_in in objs_in:
            existing_contact = db.query(self.model).filter(
                self.model.client_id == obj_in.client_id,
                self.model.contact_id == obj_in.contact_id
            ).first()
            if existing_contact:
                # Atualizar contato existente
                for key, value in obj_in.dict().items():
                    setattr(existing_contact, key, value)
                db.commit()
                db.refresh(existing_contact)
                responses.append(obj_to_dict(existing_contact))
            else:
                # Criar novo contato
                obj = self.model(**obj_in.dict())
                db.add(obj)
                db.commit()
                db.refresh(obj)
                responses.append(obj_to_dict(obj))
        return responses


class CRUDNotificationConfig(CRUDBase):
    def __init__(self):
        super().__init__(NotificationConfig)

    def update_or_create(self, db, user_id, obj_in):
        notification = db.query(self.model).filter(self.model.user_id == user_id).first()
        if not notification:
            # Criar uma nova configuração se não existir
            notification = self.model(user_id=user_id, notify_contacts=True, notify_attendant=False)
            db.add(notification)
        for key, value in obj_in.dict(exclude_unset=True).items():
            setattr(notification, key, value)
        db.commit()
        db.refresh(notification)
        return obj_to_dict(notification)


class CRUDTeam(CRUDBase):
    def __init__(self):
        super().__init__(Team)


class CRUDAttendant(CRUDBase):
    def __init__(self):
        super().__init__(Attendant)


crud_user = CRUDUser()
crud_client = CRUDClient()
crud_contact = CRUDContact()
crud_notification = CRUDNotificationConfig()
crud_team = CRUDTeam()
crud_attendant = CRUDAttendant()
