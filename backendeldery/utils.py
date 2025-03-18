from datetime import datetime, timezone
from typing import Optional

import bcrypt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery.database import db_instance


def obj_to_dict(obj, exclude_fields=None):
    """
    Converts a SQLAlchemy object to a dictionary.
    :param obj: SQLAlchemy object
    :param exclude_fields: Fields to be excluded from the dictionary
    :return: Dictionary containing the object's data
    """
    if not obj:
        return None
    exclude_fields = exclude_fields or []
    return {
        col.name: getattr(obj, col.name)
        for col in obj.__table__.columns
        if col.name not in exclude_fields
    }


def hash_password(password: Optional[str]) -> Optional[str]:
    """
    Generates a hash for a password.

    :param password: Plain text password
    :return: Password hash
    """
    if password is None:
        return None
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(
    plain_password: Optional[str], hashed_password: Optional[str]
) -> bool:
    """
    Verifies if the plain text password matches the hash.

    :param plain_password: Plain text password
    :param hashed_password: Password hash
    :return: True if the password is valid, False otherwise
    """
    if plain_password is None or hashed_password is None:
        return False
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def format_response(data=None, message="Success", status="ok"):
    """
    Formats the API response.

    :param data: Data to be returned
    :param message: Descriptive message
    :param status: Response status ('ok', 'error', etc.)
    :return: Formatted dictionary
    """
    return {"status": status, "message": message, "data": data}  # pragma: no cover


def validate_foreign_key(db: Session, model, field_name: str, value: int):
    """
    Checks if a foreign key value exists in the database.

    :param db: Database session
    :param model: Related SQLAlchemy model
    :param field_name: Name of the field to be validated
    :param value: Foreign key value
    :return: None, raises an HTTP exception if not valid
    """
    if not db.query(model).filter(getattr(model, field_name) == value).first():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid foreign key: {field_name} with value {value} does not exist.",
        )


def current_timestamp() -> str:
    """
    Returns the current timestamp in ISO 8601 format.

    :return: String with the current timestamp
    """
    return datetime.now(timezone.utc).isoformat()  # pragma: no cover


def get_db():
    """
    Dependency to get the database session.
    """
    yield from db_instance.get_db()


async def get_db_aync():
    """
    Dependency to get the database async session.
    """
    async for session in db_instance.get_async_db():
        yield session
