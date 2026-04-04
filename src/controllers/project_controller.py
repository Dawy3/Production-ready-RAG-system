from .base_controller import BaseController
import os 

class ProjectController(BaseController):
    
    def __init__(self):
        super().__init__()
        
    def get_project_path(self, project_id: str):
        """
        from the project id we add it to the project path
        """
        
        project_dir = os.path.join(
            self.files_dir,
            project_id
        )
        
        # Create if not exist and get the path
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
            
        
        return project_dir