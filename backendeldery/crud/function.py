# python
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery.crud.base import CRUDBase
from backendeldery.models import Function, Attendant


class CRUDFunction(CRUDBase):
    def __init__(self):
        super().__init__(Function)

    async def get_by_name(self, db: Session, name: str) -> Function:
        return db.query(self.model).filter(self.model.name == name).first()

    async def create(
        self, db: Session, name: str, description: str, created_by: int, user_ip: str
    ) -> Function:
        func_obj = Function(
            name=name,
            description=description,
            created_by=created_by,
            user_ip=user_ip,
            updated_by=None,
        )
        db.add(func_obj)
        db.flush()
        db.refresh(func_obj)
        return func_obj

    async def update(
        self,
        db: Session,
        func_id: int,
        update_data: dict,
        updated_by: int,
        user_ip: str,
    ) -> Function:
        func_obj = db.query(self.model).filter(self.model.id == func_id).first()
        if not func_obj:
            raise HTTPException(status_code=404, detail="Function not found")
        for field, value in update_data.items():
            setattr(func_obj, field, value)
        func_obj.updated_by = updated_by
        func_obj.user_ip = user_ip
        db.add(func_obj)
        db.commit()
        db.refresh(func_obj)
        return func_obj

    async def list_all(self, db: Session) -> List[Function]:
        functions = db.query(self.model).all()
        return functions

    async def list_attendants(self, db: Session, function_id: int) -> List[Attendant]:
        """
        Retrieves all attendants associated with the given function.
        """
        func_obj = db.query(self.model).filter(self.model.id == function_id).first()
        if not func_obj:
            raise HTTPException(status_code=404, detail="Function not found")
        return func_obj.attendants
