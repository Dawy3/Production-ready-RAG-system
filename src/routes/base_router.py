from fastapi import  APIRouter, Depends
from helpers.config import get_settings, Settings
from datetime import datetime
import time, logging
from tasks.mail_service import send_email_reports 

logger = logging.getLogger('uvicorn.error')

base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)

@base_router.get("/")
async def welcome(settings:Settings= Depends(get_settings)): 
    settings = get_settings()
    
    app_name = settings.APP_NAME
    app_version = settings.APP_VERSION
    return {
        "app_name" : app_name,
        "app_version" : app_version,
        "datetime" : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
@base_router.get("/send_reports")
async def send_reports(app_settings: Settings = Depends(get_settings)):
    
    task = send_email_reports.delay(
        mail_wait_seconds=3
    )

    return {
        "success": True,
        "task_id": task.id
    }