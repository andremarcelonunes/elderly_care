from motor.motor_asyncio import AsyncIOMotorClient

from backendeldery.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
mongo_db = client[settings.MONGO_DB]
emergency_collection = mongo_db["emergencies"]