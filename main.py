from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

from src.routes import base
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import settings

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    
    app.mongo_conn = AsyncIOMotorClient(settings.MONOGDB_URL)
    app.db_client = app.mongo_conn[settings.MONOGDB_DATABASE]

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongo_conn.close()
    
    
app.include_router(base.base_router)

