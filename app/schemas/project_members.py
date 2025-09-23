from app.models.project_members import ProjectMembers  
from pydantic import BaseModel
from typing import Optional
from app.schemas.project import ProjectOut
from enum import Enum

class ProjectMemberRole(Enum, str):
    LEADER = "leader"
    MEMBER = "member"

class ProjectMemberCreate(BaseModel):
    user_id: int  
    role: ProjectMemberRole
    
class ProjectMemberUpdate(BaseModel):
    role: ProjectMemberRole

class ProjectMemberOut(BaseModel):
    id: int
    user_id: int 
    project_id: int 
    role: ProjectMemberRole
    project: Optional[ProjectOut] = None
    
    class Config: 
        from_attributes=True
        orm_mode=True