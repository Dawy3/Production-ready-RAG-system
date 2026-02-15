from fastapi import FastAPI, APIRouter, Depends
import os
from src.helpers.config import settings

base_router= APIRouter(
    prefix="/api/v1",
    tags=["base"]
)


@base_router.get("/")
async def welcome():
        
    app_name = settings.APP_NAME
    app_version = settings.APP_VERSION 
    
    return{
        "app_name" : app_name,
        "app_version": app_version
    }