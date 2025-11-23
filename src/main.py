from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes import base, data
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    
    # Startup
    app.mongo_conn = AsyncIOMotorClient(settings.MONGO_URI)
    app.db_client = app.mongo_conn[settings.MONGODB_NAME]
    print("✅ Connected to MongoDB")
    
    yield
    
    # Shutdown
    app.mongo_conn.close()
    print("🛑 MongoDB connection closed")

app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
