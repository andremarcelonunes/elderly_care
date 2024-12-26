from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from bson import ObjectId, SON
from models import Patient
from backendeldery.database import get_db
from backendeldery.database_nosql import emergency_collection
from schemas import (
    UserCreate, PatientCreate, PatientUpdate, ContactCreate,
    EmergencyCreate, EmergencyUpdate
)
from backendeldery.crud import create_user, get_user, create_patient, update_patient, add_contact

app = FastAPI()

# Cadastrar usuário
@app.post("/users/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)

# Pesquisar usuário
@app.get("/users/{user_id}")
def get_user_info(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Criar paciente
@app.post("/patients/")
def create_patient_endpoint(patient: PatientCreate, db: Session = Depends(get_db)):
    return create_patient(db, patient)

# Consultar paciente
@app.get("/patients/{patient_id}")
def get_patient_info(patient_id: int, db: Session = Depends(get_db)):
    # Filtra o paciente pela coluna id da tabela Patient
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

# Alterar dados do paciente
@app.put("/patients/{patient_id}")
def update_patient_info(patient_id: int, patient: PatientUpdate, db: Session = Depends(get_db)):
    updated_patient = update_patient(db, patient_id, patient)
    if not updated_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return updated_patient

# Associar contato ao paciente
@app.post("/contacts/")
def add_contact_endpoint(contact: ContactCreate, db: Session = Depends(get_db)):
    return add_contact(db, contact)

# Criar emergência
@app.post("/emergencies/")
async def create_emergency(emergency: EmergencyCreate):
    result = await emergency_collection.insert_one(emergency.dict())
    return {"message": "Emergency created", "emergency_id": str(result.inserted_id)}

# Atender emergência
@app.put("/emergencies/{emergency_id}")
async def attend_emergency(emergency_id: str, update: EmergencyUpdate):
    # Certifique-se de converter o ID para ObjectId
    result = await emergency_collection.update_one(
        {"_id": ObjectId(emergency_id)},
        {"$set": {"status": update.status}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Emergency not found")

    return {"message": "Emergency updated"}

# Listar emergências por paciente
@app.get("/emergencies/patient/{patient_id}")
async def list_emergencies(patient_id: int):
    # Certifique-se de que patient_id é um inteiro e compatível com o banco
    emergencies = await emergency_collection.find({"patient_id": patient_id}).to_list(100)
    # Converter o campo _id de ObjectId para string
    for emergency in emergencies:
        emergency["_id"] = str(emergency["_id"])
    return emergencies