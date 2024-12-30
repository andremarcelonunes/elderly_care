from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import db_instance
from crud import crud_user, crud_client, crud_contact, crud_notification, crud_team, crud_attendant
from schemas import UserCreate, ClientCreate,  NotificationConfigUpdate, TeamCreate, ContactCreateMany, AttendandCreate
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
import logging

app = FastAPI()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )




def get_db():
    yield from db_instance.get_db()

@app.post("/users/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return crud_user.create(db, user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clients/register/")
def register_client(client: ClientCreate, db: Session = Depends(get_db)):
    try:
        return crud_client.create(db, client)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/contacts/register_many/")
def register_contacts(contacts: ContactCreateMany, db: Session = Depends(get_db)):
    try:
        return crud_contact.create_many(db, contacts.contacts)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/attendants/register/")
def register_attendant(attendant: AttendandCreate, db: Session = Depends(get_db)):
    try:
        attendant_data = attendant.dict()
        response = crud_attendant.create(db, attendant_data)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/teams/register/")
def register_team(team: TeamCreate, db: Session = Depends(get_db)):
    try:
        return crud_team.create(db, team)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/notifications/emergency/{client_id}")
def configure_emergency(client_id: int, config: NotificationConfigUpdate, db: Session = Depends(get_db)):
    try:
        notification = crud_notification.update_or_create(db, client_id, config)
        return notification
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))