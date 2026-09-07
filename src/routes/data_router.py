"""
Data Router:  Endpoints that controll Uplading, Processing and Saving data to DB(MongoDB, PostgreSQL, etc..)
"""

from fastapi import  APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController
from models.project_model import ProjectModel
from models.asset_model import AssetModel
from models.db_schemes import Asset
from models.enums.asset_type_enums import AssetTypeEnums
from models import ResponseSignals
import os
import logging 
import aiofiles         # Read/Write files using async/await
from tasks.file_processing import process_project_files
from .shcemes.data_schema import ProcessRequestSchemes

logger = logging.getLogger('uvicorn.error')


data_router = APIRouter(
    prefix = "/api/v1/data",
    tags= {"api_v1", "data"},
) 

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: int, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):
    
    # connection with DB client
    project_model= await ProjectModel.create_instance(        
        db_client= request.app.db_client        # Connection with url and specifiy DB'mini-rag' name : return Collection!
    )
    # Inside the MongoDB find it or create one => It's operation
    project = await project_model.get_project_or_create_one(project_id=project_id)  
    
    # Validate, create unique path and clear name if it had ambigous name EX: @assets$$$$..
    data_controller = DataController()
    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)
    
    if not is_valid:
        return JSONResponse(
            status_code= status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )
    
    
    # Generate unique file_path EX: ./8712asdf_file.pdf
    file_path , file_id = data_controller.generate_unique_filepath( 
        orig_file_name=file.filename,
        project_id=project_id       # use ProjectController function and get the path then combine them EX: assets/files/1/8712asdf_file.pdf
    )

    
    try:
        # After generating file path write binary using aiofiles by chunks in case it's large file
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
                
    except Exception as e:
        
        logger.error(f"Error while uploading file : {e}")
        return JSONResponse(
            status_code= status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignals.FILE_UPLOAD_FAILED.value
            })
    
    # Store the assets into the database
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    
    asset_resource = Asset(
        asset_project_id= project_id,  
        asset_type= AssetTypeEnums.FILE.value,
        asset_name = file_id,
        asset_size = os.path.getsize(file_path)
    )
        
    asset_record = await asset_model.create_asset(asset= asset_resource)
    
    
    
    return JSONResponse(
        content={
            "signal": ResponseSignals.FILE_UPLOAD_SUCCESS.value,
            "file_id" : str(asset_record.asset_id),
        }
    )
    
    
######################################### Processing #########################################

@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, project_id: int, process_request: ProcessRequestSchemes ):
    
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    task = process_project_files.delay(
        project_id=project_id,
        file_id=process_request.file_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
        do_reset=do_reset,
    )

    return JSONResponse(
        content={
            "signal": ResponseSignals.PROCESSING_SUCCESS.value,
            "task_id": task.id
        }
    )
    
    
    