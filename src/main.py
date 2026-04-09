from fastapi import FastAPI
from routes import base_router, data_router
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm.llm_provider_factory import LLMProviderFactor

app = FastAPI()

async def startup_db_client():
    settings = get_settings()
    
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DB]
    
    llm_provider_factor = LLMProviderFactor(settings)
    
    # Generation client
    app.generation_client = llm_provider_factor.create(settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)
    
    # embedding client
    app.embedding_client = llm_provider_factor.create(settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE)
    

async def shutdown_db_client():
    app.mongo_conn.close()
    
app.router.lifespan.on_startup.append(startup_db_client)
app.router.lifespan.on_shutdown.append(shutdown_db_client)

app.include_router(base_router.base_router) # it's route base that check out if the server is working or not 
app.include_router(data_router.data_router)