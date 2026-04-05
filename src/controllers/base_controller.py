"File for default setting and controller here mean control the routes or project functions"

from helpers.config import  get_settings
import os 
import random
import string

class BaseController:
    
    def __init__(self):
        
        self.app_settings = get_settings() 
        self.base_dir = os.path.dirname(os.path.dirname(__file__))      # The current path direction "C:/Users/Eldawy/Projects/12. mini-rag/src"
        self.files_dir = os.path.join(self.base_dir, "assets", "files") # where our files should be "assets/files"
        os.makedirs(self.files_dir, exist_ok=True) # make the previous folder path if it doesn't exist 

    def generate_random_string(self, length: int=8):
        """Generate random string in case upload the same file name"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))