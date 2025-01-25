from sqlalchemy.orm import Session
from typing import Type, TypeVar, Generic, Optional
from fastapi import HTTPException
from backendeldery.utils import  obj_to_dict

# Representa o tipo do modelo SQLAlchemy
ModelType = TypeVar("ModelType")
# Representa o tipo do schema Pydantic
CreateSchemaType = TypeVar("CreateSchemaType")


class CRUDBase(Generic[ModelType, CreateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[dict]:
        obj = db.query(self.model).filter(self.model.id == id).first()
        return obj_to_dict(obj) if obj else None

    def create(self, db: Session, obj_in: CreateSchemaType) -> dict:
        obj_data = self.model(**obj_in.dict())
        db.add(obj_data)
        db.commit()
        db.refresh(obj_data)
        return obj_to_dict(obj_data)

    def update(self, db: Session, id: int, obj_in: CreateSchemaType) -> dict:
        # Busca o objeto no banco de dados
        db_obj = db.query(self.model).filter(self.model.id == id).first()
        if not db_obj:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} with id {id} not found.")

        # Atualiza os campos dinamicamente
        for field, value in obj_in.dict(exclude_unset=True).items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return obj_to_dict(db_obj)

    def delete(self, db: Session, id: int) -> dict:
        # Busca o objeto no banco de dados
        db_obj = db.query(self.model).filter(self.model.id == id).first()
        if not db_obj:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} with id {id} not found.")

        db.delete(db_obj)
        db.commit()
        return obj_to_dict(db_obj)
