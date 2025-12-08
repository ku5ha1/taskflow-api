from app.models.projects import Project
from pydantic import BaseModel 
from datetime import datetime
from typing import List, Optional

class ProjectBase(BaseModel):
    name: str 
    description: str
    status: Optional[str] = "active"
    deadline: Optional[datetime] = None
    tags: Optional[str] = None

class ProjectCreate(BaseModel):
    name: str 
    description: str
    status: Optional[str] = "active"
    deadline: Optional[datetime] = None
    tags: Optional[str] = None
    
class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[datetime] = None
    tags: Optional[str] = None
    
class ProjectOut(ProjectBase):
    id: int  
    created_by: int 
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config: 
        from_attributes=True
        orm_mode=True

class ProjectList(BaseModel):
    projectlist: List[ProjectOut]
    
    class Config: 
        from_attributes=True
        orm_mode=True