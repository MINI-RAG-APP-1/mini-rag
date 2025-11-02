from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes import base, data
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    
    # Startup
    app.mongodb_client = AsyncIOMotorClient(settings.MONGO_URI)
    app.mongodb = app.mongodb_client[settings.MONGODB_NAME]
    print("✅ Connected to MongoDB")
    
    yield
    
    # Shutdown
    app.mongodb_client.close()
    print("🛑 MongoDB connection closed")

app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
