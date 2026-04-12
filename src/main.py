from fastapi import FastAPI
from routes import base_router, data_router, nlp_router
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm.llm_provider_factory import LLMProviderFactor
from stores.vectorDB.vectorDB_factory import VectorDBFactory

app = FastAPI()

async def startup_span():
    settings = get_settings()
    
    # DB Client
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DB]
    
    # LLM Factory
    llm_provider_factor = LLMProviderFactor(settings)
    
    # VectorDB Factory
    vector_db_factory = VectorDBFactory(settings) 
    
    # Generation client
    app.generation_client = llm_provider_factor.create(settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)
    
    # embedding client
    app.embedding_client = llm_provider_factor.create(settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE)
    
    # vector db client
    app.vectordb_client = vector_db_factory.create(provider=settings.VECTOR_DB_BACKEND)
    app.vectordb_client.connect()
    
    
async def shutdown_span():
    app.mongo_conn.close()
    app.vectordb_client.disconnect()
    
app.add_event_handler("startup", startup_span)
app.add_event_handler("shutdown", shutdown_span)


app.include_router(base_router.base_router) # it's route base that check out if the server is working or not 
app.include_router(data_router.data_router)
app.include_router(nlp_router.nlp_router)