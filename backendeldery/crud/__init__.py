from .users import crud_user,    crud_client,    crud_contact,   crud_attendant
from .base import CRUDBase


__all__ = ["CRUDBase", "crud_user", "crud_client", "crud_contact", "crud_attendant"]