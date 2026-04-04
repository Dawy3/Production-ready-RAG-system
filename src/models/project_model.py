from .base_data_model import BaseDataModel
from .db_shcemes import Project
from .enums.data_base_enums import DataBaseEnum


class ProjectModel(BaseDataModel):
    
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value] # Projects
        
    
    async def create_proejct(self, project: Project):
        result = await self.collection.insert_one(project.dict(by_alias=True, exclude_unset=True))
        project.id = result.inserted_id
        
        return project
    
    async def get_project_or_create_one(self, project_id: str):
        
        record = await self.collection.find_one({
            "project_id" : project_id 
        })
        if not record:
            # Create new project
            project = Project(project_id=project_id) # create object
            project = await self.create_proejct(project=project)
        
            return project
        
        return Project(**record) # give every value on record to create 
    
    async def get_all_projects(self, page: int=1, page_size: int=10):
        
        # Count total number of documents
        total_documents = await self.collection.count_documents({}) # {} means no filter → count everything.
        
        # Calculate total number of pages
        total_pages = total_documents // page_size
        if total_documents % page_size > 0:
            total_pages += 1
            
        cursor = self.collection.find().skip((page-1) * page_size ).limit(page_size)
        projects = []
        async for document in cursor:
            projects.append(
                Project(**document)
            )
            
        return projects , total_pages
            
        
    
    
    
        
    