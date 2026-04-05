"""
Handles project-related database operations.

Supports creating projects, retrieving or creating a project by ID,
and fetching projects with pagination using skip() and limit().

Uses ProjectSchemes for data validation and async MongoDB operations.
"""



from .base_data_model import BaseDataModel
from .db_schemes import ProjectSchemes
from .enums.DB_enums import DataBaseEnum


class ProjectModel(BaseDataModel):
    
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value] # Projects
        
    
    async def create_proejct(self, project: ProjectSchemes):
        result = await self.collection.insert_one(project.dict(by_alias=True, exclude_unset=True))
        project.id = result.inserted_id
        
        return project
    
    async def get_project_or_create_one(self, project_id: str):
        
        record = await self.collection.find_one({
            "project_id" : project_id 
        })
        if not record:
            # Create new project
            project = ProjectSchemes(project_id=project_id)         # Check project id 
            project = await self.create_proejct(project=project)    # then create one 
        
            return project
        
        return ProjectSchemes(**record) # give every value on record to check
    
    async def get_all_projects(self, page: int=1, page_size: int=10):
        """
        Fetch all projects from the database but not all at once. A list of projects for the current page & Total number of pages
        """
        
        # Count total number of documents
        total_documents = await self.collection.count_documents({}) # {} means no filter, so it counts everything in the collection
        
        # Calculate total number of pages
        total_pages = total_documents // page_size      # How mange pages   
        if total_documents % page_size > 0:             # if it exceed page_size then add one more page
            total_pages += 1
            
        cursor = self.collection.find().skip((page-1) * page_size ).limit(page_size) # skip the previous pages, then take only this page
        projects = []
        async for document in cursor:
            projects.append(
                ProjectSchemes(**document)
            )
            
        return projects , total_pages   # a list of project for the current page - Total number of pages
            
        
    
    
    
        
    