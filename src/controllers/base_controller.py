"File for default setting and controller here mean control the routes or project functions"

from helpers.config import  get_settings
import os 
import random
import string

class BaseController:
    
    def __init__(self):
        
        self.app_settings = get_settings() 
        self.base_dir = os.path.dirname(os.path.dirname(__file__)) # get file direction
        self.files_dir = os.path.join(self.base_dir, "assets", "files") # where our files should be 
        os.makedirs(self.files_dir, exist_ok=True) # make file direction 

    def generate_random_string(self, length: int=12):
        """
        Generate random string name to give it to data controller in case there's a client that abloud the same file or same name 
        """
        return ' '.join(random.choices(string.ascii_lowercase + string.digits, k=length))