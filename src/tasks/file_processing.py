from celery_app import celery_app, get_setup_utils
from helpers.config import get_settings
import asyncio
from models.project_model import ProjectModel
from models.db_schemes import DataChunk, Asset
from models.chunk_model import ChunkModel
from models.asset_model import AssetModel
from models.enums.asset_type_enums import AssetTypeEnums
from controllers import NLPController
from models import ResponseSignals
import logging
from controllers import DataController,  ProcessController



logger = logging.getLogger('celery.task')

@celery_app.task(bind=True, name="tasks.file_processing.process_project_files",
                autoretry_for=(Exception,),
                retry_kwargs={"max_retries": 3, "countdown": 60})
def process_project_files(self, project_id: int, file_id: str = None,
                          chunk_size: int = 100, overlap_size: int = 20,
                          do_reset: int = 0):
    return asyncio.run(
        _process_projects_file(self, project_id, file_id,
                               chunk_size, overlap_size, do_reset)
    )


async def _process_projects_file(task_instance, project_id, file_id,
                                 chunk_size, overlap_size, do_reset):
    
    db_engine, vectordb_client = None, None
    try:
        (db_engine, db_client, llm_provider_factor, 
        vector_db_factory, generation_client, 
        embedding_client, vectordb_client, template_parser ) = await get_setup_utils()
        # connection with DB client
        project_model= await ProjectModel.create_instance(        
            db_client= db_client        # Connection with url and specifiy DB'mini-rag' name : return Collection!
        )
        project = await project_model.get_project_or_create_one(project_id=project_id)  
        
        nlp_controller = NLPController(
            vectordb_client=vectordb_client,
            generation_client=generation_client,
            embedding_client= embedding_client,
            template_parser= template_parser
        )
        
        asset_model = await AssetModel.create_instance(                                 
            db_client= db_client
        )

        project_files_ids = {}
        
        if file_id:
            asset_record = await asset_model.get_asset_record(
                asset_project_id=project_id,
                asset_name= file_id
            )
            if  asset_record == None:
                task_instance.update_state(
                    state="FAILURE",
                    meta={
                        "signal": ResponseSignals.FILE_ID_ERROR.value
                    }
                ) 

                raise Exception(f"No assets for file:{file_id}")
            project_files_ids = {
                asset_record.asset_id: asset_record.asset_name
            }
                
        else:
            
            project_files = await asset_model.get_all_project_assets(       # Get all project_id 
                asset_project_id=project_id,
                asset_type=AssetTypeEnums.FILE.value,
            )
            project_files_ids = {                                           # from project_ids get list of all asset_name (files_name)
                record.asset_id: record.asset_name
                for record in project_files
            }
            
        if len(project_files_ids) ==0:                                      # Empty? Raise error
            
            task_instance.update_state(
                state="FAILURE",
                meta={
                    "signal": ResponseSignals.NO_FILES_ERROR.value,
                }
            )

            raise Exception(f"No filed found for project_id: {project.project_id}")

            
        process_controller = ProcessController(project_id=project_id)       # here the prcoess main functions 
        num_records = 0
        num_files = 0
        
        chunk_model = await ChunkModel.create_instance(
            db_client = db_client
        )
        
        if do_reset == 1:
            # Delete associated vectors collection
            collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
            _ = await vectordb_client.delete_collection(collection_name=collection_name)
            
            # Delete associated chunks
            _ = await chunk_model.delete_chunks_by_project_id(project_id=project.project_id)
            
        for asset_id, file_id in project_files_ids.items():                                   # Run a loop for each file_id in dictionary .items()
            
            file_content = process_controller.get_file_content(file_id=file_id) # get fild_id return loaded data with text & metadata
            
            if file_content is None:
                logger.error(f"Error while processing file: {file_id}")
                continue
            
            file_chunks = process_controller.process_file_content(  # Recrusve_chunker give the (txt + metadata) - chunk_size - overlap and chunk
                file_content=file_content,
                chunk_size= chunk_size,
                overlap_size=overlap_size
            )
            
            if file_chunks is None or len(file_chunks) == 0:            # is everything ok?

                logger.error(f"No chunks fo file_id: {file_id}")
                pass
            
            file_chunks_record = [
                DataChunk(
                    chunk_text=chunk.page_content,
                    chunk_metadata= chunk.metadata,
                    chunk_order= i+1,
                    chunk_project_id= project_id,
                    chunk_asset_id=asset_id
                )
                for i, chunk in enumerate(file_chunks)
            ]
            
            num_records += await chunk_model.insert_many_chunks(chunks= file_chunks_record)
            num_files += 1
        
        task_instance.update_state(
            state="SUCCESS",
            meta={
                "signal": ResponseSignals.NO_FILES_ERROR.value,
            }
        )
        return {
                "signal": ResponseSignals.PROCESSING_SUCCESS.value,
                "inserted_chunks": num_records,
                "processed_files" : num_files
            }
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        raise
    finally:
        try:
            if db_engine:
                await db_engine.dispose()
            
            if vectordb_client:
                await vectordb_client.disconnect()
        except Exception as e:
            logger.error(f"Task failed while clean: {str(e)}")
    


