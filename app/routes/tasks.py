from sqlalchemy.orm import Session
from app.utils.dependencies import get_db, get_current_active_user
from app.models.tasks import Task
from app.models.user import User
from app.models.project_members import ProjectMembers
from app.schemas.project_members import ProjectMemberRole
from app.schemas.tasks import TaskCreate, TaskOut, TaskList, TaskUpdate, TaskStatus, TaskStatusUpdate, TaskPriority
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
import datetime

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Tasks"])


def leader_or_admin_required(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Verify user is admin or project leader"""
    if not current_user.is_admin:
        # Additional project-specific checks would go here
        pass
    return current_user


def can_view_task(
    project_id: int,
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Task:
    """Verify user can view the task"""
    db_task = db.query(Task).filter(
        Task.id == task_id,
        Task.project_id == project_id
    ).first()
    
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Admin can view all tasks
    if current_user.is_admin:
        return db_task
    
    # Check if user is project member
    membership = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id,
        ProjectMembers.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this task"
        )
    
    return db_task


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: int,
    task_data: TaskCreate,
    current_user: User = Depends(leader_or_admin_required),
    db: Session = Depends(get_db)
):
    """Create a new task in project - POST /projects/{project_id}/tasks"""
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all tasks in project with filters - GET /projects/{project_id}/tasks"""
    is_leader = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id,
        ProjectMembers.user_id == current_user.id,
        ProjectMembers.role == ProjectMemberRole.LEADER.value
    ).first()

    if not is_leader and not current_user.is_admin:
        if assigned_to and assigned_to != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own tasks"
            )
        assigned_to = current_user.id

    query = db.query(Task).filter(
        Task.project_id == project_id
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
    db_task: Task = Depends(can_view_task)
):
    """Get single task by ID - GET /projects/{project_id}/tasks/{task_id}"""
    return db_task


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    project_id: int,
    task_id: int,
    new_task_data: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(leader_or_admin_required),
    db: Session = Depends(get_db)
):
    """Delete task - DELETE /projects/{project_id}/tasks/{task_id}"""
    db_task = db.query(Task).filter(
        Task.project_id == project_id,
        Task.id == task_id
    ).first()
    
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    db.delete(db_task)
    return None
