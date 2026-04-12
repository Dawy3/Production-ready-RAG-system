from .providers import QdrantDB
from .vectorDB_enums import VectordbEnums
from controllers.base_controller import BaseController

class VectorDBFactory:
    def __init__(self, config):
        self.config = config
        self.base_controller = BaseController() 
        
    def create(self, provider: str):
        if provider == VectordbEnums.QDRANT.value:
            db_path = self.base_controller.get_database_path(db_name=self.config.VECTOR_DB_PATH)
            return QdrantDB(
                db_path= db_path,
                distance_method = self.config.VECTOR_DB_DISTANCE_METHOD
            )
            
        return None
    