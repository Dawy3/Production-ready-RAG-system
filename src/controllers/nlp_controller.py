from .base_controller import BaseController
from db_models.db_schemes import ProjectSchemes, DataChunkSchemes
from stores.llm.llm_enums import DocumentTypeEnum
from typing import List
import json

class NLPController(BaseController):
    
    def __init__(self, vectordb_client, generation_client, embedding_client):
        super().__init__()
        
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        
    
    def create_collection_name(self, projecet_id: str):
        return f"collection_{projecet_id}".strip()
    
    def reset_vector_db_collection(self, project: ProjectSchemes):
        collection_name = self.create_collection_name(projecet_id= project.project_id)
        return self.vectordb_client.delete_collection(collection_name)
    
    def get_vector_db_collection_info(self, project: ProjectSchemes):
        collection_name = self.create_collection_name(projecet_id= project.project_id)
        collection_info =  self.vectordb_client.get_collection_info(collection_name)
        
        return json.loads(  # Turn it to json
            json.dumps(collection_info, default= lambda x: x.__dict__)  # Turn Collection info to string -> convert  the objects into dict type
        )
    
    def index_into_vector_db(self, project: ProjectSchemes, chunks: List[DataChunkSchemes],
                             chunks_ids: List[int], do_reset: bool=False):
        # Step1: get collection name
        collection_name = self.create_collection_name(projecet_id=project.project_id)
        
        # Step2: Mange Items
        texts = [ c.chunk_text for c in chunks]
        metadata = [c.chunk_metadata for c in chunks]
        
        vectors = [
            self.embedding_client.embed_text(text, DocumentTypeEnum.DOCUMENT.value)
            for text in texts
        ]
        
        # Step3: Create collection if not exists
        _ = self.vectordb_client.create_collection(
            collection_name= collection_name,
            do_reset=do_reset,
            embedding_size = self.embedding_client.embedding_size,
        )
            
        # Step4: insert into VectorDB
        _ = self.vectordb_client.insert_many(
            collection_name = collection_name,
            texts= texts,
            vectors= vectors,
            metadata=metadata,
            record_ids = chunks_ids
        )
        
        return True
    
    def search_vector_db_collection(self, project: ProjectSchemes, text: str, limit: int=10):
        
        # step1 : get collection name
        collection_name = self.create_collection_name(projecet_id=project.project_id)
        
        # step2 : get text embedding vector
        vector = self.embedding_client.embed_text(text, DocumentTypeEnum.QUERY.value)
        
        if not vector or len(vector) == 0:
            return False
        
        # step3 : do semantic search
        results = self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            vector= vector,
            limit=limit
        )
        
        if not results:
            return False
        
        return json.loads(
            json.dumps(results, default=lambda x: x.__dict__)
        )
        