from fastapi import FastAPI, APIRouter, Depends, UploadFile
import os
from src.helpers.config import settings


data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"]
)

