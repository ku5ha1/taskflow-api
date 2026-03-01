from sqlalchemy.orm import Session
from app.utils.dependencies import get_db, get_current_active_user
from app.utils.permissions import RoleChecker
from app.models.tasks import Task
from app.models.user import User
from app.models.project_members import ProjectMembers
from app.schemas.project_members import ProjectMemberRole
from app.schemas.tasks import TaskCreate, TaskOut, TaskList, TaskUpdate, TaskStatus, TaskStatusUpdate, TaskPriority
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
import datetime

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Tasks"])


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: int,
    task_data: TaskCreate,
    current_user: User = Depends(RoleChecker("task:create", "project_id")),
    db: Session = Depends(get_db)
):
    """Create a new task in project (admin or leader) - POST /projects/{project_id}/tasks"""
    membership = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id,
        ProjectMembers.id == task_data.assigned_to_user
    ).first()

    if not membership:
        membership = db.query(ProjectMembers).filter(
            ProjectMembers.project_id == project_id,
            ProjectMembers.user_id == task_data.assigned_to_user
        ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project membership not found for the provided assignee"
        )

    new_task = Task(
        project_id=project_id,
        name=task_data.name,
        description=task_data.description,
        status=TaskStatus.PENDING.value,
        priority=task_data.priority,
        due_date=task_data.due_date,
        assigned_to_user=membership.id,
        estimated_hours=task_data.estimated_hours,
        actual_hours=task_data.actual_hours,
        tags=task_data.tags,
        attachments=task_data.attachments
    )
    db.add(new_task)
    db.flush()
    db.refresh(new_task)
    
    return new_task


@router.get("", response_model=TaskList)
async def list_tasks(
    project_id: int,
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    priority: Optional[TaskPriority] = Query(None),
    assigned_to: Optional[int] = Query(None),
    due_before: Optional[str] = Query(None),
    due_after: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    offset: Optional[int] = Query(None),
    current_user: User = Depends(RoleChecker("task:view", "project_id")),
    db: Session = Depends(get_db)
):
    """List all tasks in project with filters - GET /projects/{project_id}/tasks"""
    query = db.query(Task).filter(
        Task.project_id == project_id,
        Task.is_deleted == False
    )

    if status_filter is not None:
        query = query.filter(Task.status == status_filter.value)
    if priority is not None:
        query = query.filter(Task.priority == priority.value)
    if assigned_to is not None:
        query = query.filter(Task.assigned_to_user == assigned_to)

    if due_before is not None:
        try:
            due_before_dt = datetime.datetime.fromisoformat(due_before)
            query = query.filter(Task.due_date < due_before_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format for due_before. Use YYYY-MM-DD"
            )

    if due_after is not None:
        try:
            due_after_dt = datetime.datetime.fromisoformat(due_after)
            query = query.filter(Task.due_date > due_after_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format for due_after. Use YYYY-MM-DD"
            )

    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)

    tasks = query.all()
    return {"tasks": tasks}


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    project_id: int,
    task_id: int,
    current_user: User = Depends(RoleChecker("task:view", "project_id")),
    db: Session = Depends(get_db)
):
    """Get single task by ID - GET /projects/{project_id}/tasks/{task_id}"""
    db_task = db.query(Task).filter(
        Task.id == task_id,
        Task.project_id == project_id
    ).first()
    
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return db_task


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    project_id: int,
    task_id: int,
    new_task_data: TaskUpdate,
    current_user: User = Depends(RoleChecker("task:update", "project_id")),
    db: Session = Depends(get_db)
):
    """Update task - PUT /projects/{project_id}/tasks/{task_id}"""
    db_task = db.query(Task).filter(
        Task.id == task_id,
        Task.project_id == project_id
    ).first()
    
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task does not exist"
        )
    
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
    if new_task_data.estimated_hours is not None:
        db_task.estimated_hours = new_task_data.estimated_hours
    if new_task_data.actual_hours is not None:
        db_task.actual_hours = new_task_data.actual_hours
    if new_task_data.tags is not None:
        db_task.tags = new_task_data.tags
    if new_task_data.attachments is not None:
        db_task.attachments = new_task_data.attachments
    
    db.flush()
    db.refresh(db_task)
    
    return db_task


@router.patch("/{task_id}/status", response_model=TaskOut)
async def update_task_status(
    project_id: int,
    task_id: int,
    task_status: TaskStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update task status - PATCH /projects/{project_id}/tasks/{task_id}/status"""
    db_task = db.query(Task).filter(
        Task.id == task_id,
        Task.project_id == project_id
    ).first()
    
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify user is assigned to this task
    membership = db.query(ProjectMembers).filter(
        ProjectMembers.id == db_task.assigned_to_user
    ).first()
    
    if not membership or membership.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not permitted to modify this task's status"
        )
    
    db_task.status = task_status.status.value
    db.flush()
    db.refresh(db_task)
    
    return db_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    project_id: int,
    task_id: int,
    current_user: User = Depends(RoleChecker("task:delete", "project_id")),
    db: Session = Depends(get_db)
):
    """Soft delete task (admin or leader) - DELETE /projects/{project_id}/tasks/{task_id}"""
    db_task = db.query(Task).filter(
        Task.project_id == project_id,
        Task.id == task_id,
        Task.is_deleted == False
    ).first()
    
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    db_task.is_deleted = True
    db_task.deleted_at = datetime.datetime.utcnow()
    db_task.deleted_by = current_user.id
    db.flush()
    
    return None
