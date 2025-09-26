from pydantic import BaseModel, Field
import enum 
from typing import Optional, List
from datetime import datetime

class TaskPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    
class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    
class TaskCreate(BaseModel):
    name: str 
    description: str 
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority 
    due_date: datetime 
    project_id: int 
    assigned_to_user: int

class TaskOut(BaseModel):
    id: int 
    name: str 
    description: str
    status: TaskStatus
    priority: TaskPriority 
    due_date: datetime 
    project_id: int 
    assigned_to_user: int
    
class TaskUpdate(BaseModel):
    name: Optional[str] = None 
    description: Optional[str] = None
    status: Optional[TaskStatus] = None 
    priority: Optional[TaskPriority] = None 
    due_date: Optional[datetime] = None
    
class TaskList(BaseModel):
    tasks: List[TaskOut]
    
class TaskStatusUpdate(BaseModel):
    status: TaskStatus