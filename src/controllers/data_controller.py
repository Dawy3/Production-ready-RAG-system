from .base_controller import BaseController
from fastapi import UploadFile
from models import ResponseSignals
from .project_controller import ProjectController
import os
import re

class DataController(BaseController):
    
    def __init__(self):
        super().__init__()
        self.size_scale = 1048576 # Convert MB to Bytes 
        
    def validate_uploaded_file(self, file: UploadFile):
        """Validate the file if it's wrong type or excceded size"""
        
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignals.FILE_TYPE_NOT_SUPPORTED.value
        
        if file.size > self.app_settings.FILE_MAX_SIZE * self.size_scale:
            return False, ResponseSignals.FILE_SIZE_EXCEEDED.value
        
        return True, ResponseSignals.FILE_UPLOAD_SUCCESS.value
    
    def generate_unique_filename(self, orig_file_name:str, project_id: str):
        """Generate unique filename in case someone upload the same file"""
        
        random_key = self.generate_random_string() # Any random string "the function on base controller"
        project_path = ProjectController().get_project_path(project_id) # it's based project so project controller and for unique file we give it project_Id
        
        cleaned_file_name = self.get_clean_file_name(orig_file_name=orig_file_name) # just clean it 
        
        new_file_path = os.path.join(
            project_path, 
            random_key + "_" + cleaned_file_name
        )
        
        while os.path.exists(new_file_path):
            random_key = self.generate_random_string() 
            new_file_path = os.path.join(
                project_path,   
                random_key + "_" + cleaned_file_name
            )
        
        return new_file_path
        
    def get_clean_file_name(self, orig_file_name: str):
        
        # remove any special characters, except underscore and .
        cleaned_file_name = re.sub(r'[^\w.]', '', orig_file_name.strip())
        
        # Replace spaces with underscore
        cleaned_file_name = cleaned_file_name.replace(" ", "_")
        
        return cleaned_file_name 
    
    