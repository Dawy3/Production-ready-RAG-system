"""
Data Router:  Endpoints that controll Uplading, Processing and Saving data to DB(MongoDB, PostgreSQL, etc..)
"""

from fastapi import  APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
from db_models.project_model import ProjectModel
from db_models.db_schemes import DataChunkSchemes
from db_models.chunk_model import ChunkModel
from db_models import ResponseSignals
from .shcemes.data_schema import ProcessRequest
import logging 
import aiofiles


logger = logging.getLogger('uvicorn.error')


data_router = APIRouter(
    prefix = "/api/v1/data",
    tags= {"api_v1", "data"},
) 

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):
    
    
    project_model = ProjectModel(
        db_client=request.app.db_client
    )
    
    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )
    
    
    # Validate the file properties
    data_controller = DataController()
    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)
    
    if not is_valid:
        return JSONResponse(
            status_code= status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )
        
    project_dir_path =  ProjectController().get_project_path(project_id=project_id)
    file_path, file_id  = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
    )
    
    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        
        logger.error(f"Error while uploading file : {e}")
        return JSONResponse(
            status_code= status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignals.FILE_UPLOAD_FAILED.value
            }
        )
        
    return JSONResponse(
        content={
            "signal": ResponseSignals.FILE_UPLOAD_SUCCESS.value,
            "file_id" : file_id
        }
    )
    
@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, project_id: str, process_request: ProcessRequest ):
    
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset
    
    project_model = ProjectModel(
        db_client=request.app.db_client
    )
    
    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )
    
        
        
    process_controller = ProcessController(project_id=project_id) # here the prcoess main functions 
    
    file_content = process_controller.get_file_content(file_id=file_id) # get fild_id return loaded data with text & metadata
    
    file_chunks = process_controller.process_file_content(  # Recrusve_chunker give the (txt + metadata) - chunk_size - overlap and chunk
        file_content=file_content,
        chunk_size= chunk_size,
        overlap_size=overlap_size
    )
    
    if file_chunks is None or len(file_chunks) == 0:            # is everything ok?
        return JSONResponse(
            status_code= status.HTTP_400_BAD_REQUEST,
            content={
                "signal" : ResponseSignals.PROCESSING_FAILED.value
            }
        )
    
    file_chunks_record = [
        DataChunkSchemes(
            chunk_text=chunk.page_content,
            chunk_metadata= chunk.metadata,
            chunk_order= i+1,
            chunk_project_id= project.id,
        )
        for i, chunk in enumerate(file_chunks)
    ]
    
     
    chunk_model = ChunkModel(
        db_client = request.app.db_client
    )
    
    if do_reset == 1:
        _ = await chunk_model.delete_chunks_by_project_id(project_id=project.id)
           
    num_records = await chunk_model.insert_many_chunks(chunks= file_chunks_record)

    return JSONResponse(
        content={
            "signal": ResponseSignals.PROCESSING_SUCCESS.value,
            "inserted_chunks": num_records,
        }
    )