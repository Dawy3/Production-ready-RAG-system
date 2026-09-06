from celery import Celery
from helpers.config import get_settings
from stores.llm.llm_provider_factory import LLMProviderFactor
from stores.vectorDB.vectorDB_factory import VectorDBFactory
from stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

settings = get_settings()

async def get_setup_utils():
    settings = get_settings()
    
    # DB Client
    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
    
    db_engine = create_async_engine(postgres_conn)
    
    db_client = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False,
    )
    
    # LLM Factory
    llm_provider_factor = LLMProviderFactor(settings)
    
    # VectorDB Factory
    vector_db_factory = VectorDBFactory(config=settings, db_client=db_client) 
    
    # Generation client
    generation_client = llm_provider_factor.create(settings.GENERATION_BACKEND)
    generation_client.set_generation_model(settings.GENERATION_MODEL_ID)
    
    # Embedding client
    embedding_client = llm_provider_factor.create(settings.EMBEDDING_BACKEND)
    embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE)
    
    # Vector db client
    vectordb_client = vector_db_factory.create(provider=settings.VECTOR_DB_BACKEND)
    await vectordb_client.connect()
    
    template_parser = TemplateParser(
        language=settings.PRIMARY_LANG,
        default_language=settings.DEFAULT_LANG,
    )

    return (db_engine, db_client, llm_provider_factor, vector_db_factory,
            generation_client, embedding_client, vectordb_client, template_parser )


# Create celery Application instance
celery_app = Celery(
    "minirag",
    broker= settings.CELERY_BROKER_URL,
    backend= settings.CELERY_RESULT_BACKEND,
    include=[
        "tasks.file_processing",
    ]
)

# Configuration Celery with essential settings
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=[
        settings.CELERY_TASK_SERIALIZER
    ],
    
    # Task Safety - late Acknowledgement prevents task loss on worker crash
    task_acks_late=settings.CELERY_TASK_ACKS_LATE,

    # Time limits - Prevent hanging tasks
    task_time_limit =settings.CELERY_TASK_TIMELIMIT,

    # Result backend - Store results for status tracking 
    task_ignore_result= False,
    result_expires= 3600,

    # Worker settings
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,

    # connection settings for better reliability
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    worker_cancel_long_running_tasks_on_connection_loss=True,

    task_routes={
        "tasks.file_processing.process_project_files": {"queue":"file_processing"},
    }
)

celery_app.conf.task_default_queue= "default"
