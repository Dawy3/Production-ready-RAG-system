"""
The file define the file extension for the document_loader then load the content cut it to "chunks" with metadata 
"""

from .base_controller import BaseController
from .project_controller import ProjectController
import os
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from db_models import ProcessingEnums




class ProcessController(BaseController):
    
    def __init__(self, project_id: str):
        super().__init__()
        
        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id)
        
    def get_file_extension(self, file_id: str):
        return os.path.splitext(file_id)[-1] # txt, pdf, doc
    
    def get_file_loader(self, file_id : str):
        """
        Choose file loader based file extension
        """
        
        file_ext = self.get_file_extension(file_id=file_id)
        file_path = os.path.join(       # Combine both project path and file id
            self.project_path,
            file_id
        )
        if not os.path.exists(file_path):
            return None
        
        if file_ext == ProcessingEnums.TXT.value:
            return TextLoader(file_path, encoding="utf-8")
        
        if file_ext == ProcessingEnums.PDF.value:
            return PyMuPDFLoader(file_path)
        
        return None
        
    def get_file_content(self, file_id:str):
        loader = self.get_file_loader(file_id=file_id)
        if loader :
            return loader.load()

        return None
    
    def process_file_content(self, file_content: list,
                             chunk_size: int=100, overlap_size: int=20):
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap= overlap_size,
            length_function= len,
        )
        
        file_content_text = [
            rec.page_content
            for rec in file_content
        ]
        
        file_content_metadata = [
            rec.metadata
            for rec in file_content
        ]
        
        chunks = text_splitter.create_documents(
            file_content_text, 
            metadatas=file_content_metadata
        )
        
        return chunks
        
    