from sqlalchemy.orm import Session
from typing import Type, TypeVar, Generic
from utils import  obj_to_dict

# Representa o tipo do modelo SQLAlchemy
ModelType = TypeVar("ModelType")
# Representa o tipo do schema Pydantic
CreateSchemaType = TypeVar("CreateSchemaType")

class CRUDBase(Generic[ModelType, CreateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int):
        obj = db.query(self.model).filter(self.model.id == id).first()
        return obj_to_dict(obj) if obj else None

    def create(self, db: Session, obj_in: CreateSchemaType):
        obj_data = self.model(**obj_in.dict())
        db.add(obj_data)
        db.commit()
        db.refresh(obj_data)
        return obj_to_dict(obj_data)

    def update(self, db: Session, db_obj: ModelType, obj_in: CreateSchemaType):
        for field, value in obj_in.dict(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return obj_to_dict(db_obj)

    def delete(self, db: Session, id: int):
        obj = db.query(self.model).filter(self.model.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj_to_dict(obj) if obj else None