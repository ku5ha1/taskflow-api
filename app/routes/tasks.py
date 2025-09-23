from sqlalchemy.orm import Session 
from app.utils.database import get_db 
from app.utils.depedency import leader_or_admin_required, get_current_user, can_view_task
from app.models.tasks import Task 
from app.models.user import User 
from app.models.project_members import ProjectMembers
from app.schemas.project_members import ProjectMemberRole
from app.schemas.tasks import TaskCreate, TaskOut, TaskList, TaskUpdate, TaskStatus, TaskStatusUpdate, TaskPriority
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import datetime

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Project Tasks"])

@router.post("/create", response_model=TaskOut)
async def create_task(
    project_id: int,
    task_data: TaskCreate,
    current_user: User = Depends(leader_or_admin_required),
    db: Session = Depends(get_db)
):
    membership_exists = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id,
        ProjectMembers.user_id == task_data.assigned_to
    ).first()
    if not membership_exists:
        raise HTTPException(
            status_code=404,
            detail="Project or member does not exist"
        )
    try:
        new_task = Task(
        project_id = project_id,
        name = task_data.name,
        description = task_data.description,
        status = TaskStatus.PENDING.value,
        priority = task_data.priority, 
        due_date = task_data.due_date,
        assigned_to = task_data.assigned_to
    )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return new_task
    
    except Exception as e:
        db.rollback()
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=500,
            detail="Could not assign task"
        )
        
@router.put("/update/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int, 
    new_task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_task = db.query(Task).filter(
        Task.id == task_id
    ).first()
    if not db_task:
        raise HTTPException(
            status_code=404,
            detail=f"Task does not exist"
        )
    try:
        if new_task_data.name is not None:
            db_task.name = new_task_data.name
        if new_task_data.description is not None:
            db_task.description = new_task_data.description
        if new_task_data.status is not None:
            db_task.status = new_task_data.status
        if new_task_data.priority is not None:
            db_task.priority = new_task_data.priority
        if new_task_data.due_date is not None:
            db_task.due_date = new_task_data.due_date 
        db.commit()
        db.refresh(db_task)
        
        return db_task 
    
    except Exception as e:
        db.rollback()
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=500,
            detail="Could not update task"
        )
        
@router.patch("/{task_id}/status")
async def modify_task_status(
    project_id: int,
    task_id: int,
    task_status: TaskStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_task = db.query(Task).filter(
        Task.id == task_id,
        Task.project_id == project_id
    ).first()
    if not db_task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    if db_task.assigned_to != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not permitted to modify this task's status."
        )
    try:
        db_task.status = task_status.status.value
        db.commit()
        db.refresh(db_task)
        
        return db_task 
    
    except Exception as e:
        db.rollback()
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=500,
            detail="Could not modify task"
        )
        
@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    db_task: Task = Depends(can_view_task),
):
    return db_task 

import datetime

@router.get("/", response_model=TaskList) 
async def get_all_tasks(
    project_id: int,
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    assigned_to: Optional[int] = Query(None),
    due_before: Optional[str] = Query(None),
    due_after: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    offset: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    is_leader = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id,
        ProjectMembers.user_id == current_user.id,
        ProjectMembers.role == ProjectMemberRole.LEADER.value
    ).first()
    
    if not is_leader and not current_user.is_admin:
        if assigned_to and assigned_to != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only view your own tasks."
            )
        assigned_to = current_user.id
        
    query = db.query(Task).filter(
        Task.project_id == project_id
    )

    if status is not None:
        query = query.filter(Task.status == status.value)
    if priority is not None:
        query = query.filter(Task.priority == priority.value) 
    if assigned_to is not None:
        query = query.filter(Task.assigned_to == assigned_to)
        
    if due_before is not None:
        try:
            due_before_dt = datetime.datetime.fromisoformat(due_before)
            query = query.filter(Task.due_date < due_before_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format for due_before. Use YYYY-MM-DD.")
            
    if due_after is not None: 
        try:
            due_after_dt = datetime.datetime.fromisoformat(due_after)
            query = query.filter(Task.due_date > due_after_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format for due_after. Use YYYY-MM-DD.")

    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
        
    tasks = query.all()
    
    return tasks

@router.delete("/delete/{task_id}")
async def delete_task(
    project_id: int, 
    task_id: int,
    current_user: User = Depends(leader_or_admin_required),
    db: Session = Depends(get_db)
):
    db_task = db.query(Task).filter(
        Task.project_id == project_id,
        Task.id == task_id
    ).first()
    if not db_task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    try:
        db.delete(db_task)
        db.commit()
    
        return {
            "message": "Task deleted succesfully"
        }
    except Exception as e:
        db.rollback()
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=500,
            detail="Could not delete task"
        )