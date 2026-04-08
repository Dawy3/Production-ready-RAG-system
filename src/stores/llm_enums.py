"""Enum: is a place we store any constent in our system."""
from enum import Enum

class LLMEnums(Enum):
    
    OPENAI = "OPENAI"
    COHERE = "COHERE"
    
class OpenAIEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    
