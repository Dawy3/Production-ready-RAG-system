"""
Project schema that structure or blueprint of a database. In plain english how data is stored and related
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from bson.objectid import ObjectId


class ProjectSchemes(BaseModel):
    id: Optional[ObjectId] = Field(None, alias= "_id")
    project_id: str = Field(..., min_length=1)

    @field_validator('project_id')                                   # Whenever someone passes {project_id} Validate it by ⬇️
    def validate_project_id(cls, value):                             # EX: class: ProjectSchemes - Value: abc123
        if not value.isalnum():                                      # Only letters (a-z, A-Z) and numbers(0-9)
            raise ValueError('project_id must be alphanumeric')
        return value

    model_config = {"arbitrary_types_allowed": True}                 # It's ok using types "Pydantic" don't understand (ObjectID)
    