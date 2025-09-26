from app.utils.auth import get_current_user
from fastapi import Depends, HTTPException 
from app.models.user import User 
from sqlalchemy.orm import Session 
from app.models.project_members import ProjectMembers
from app.schemas.project_members import ProjectMemberRole
from app.models.tasks import Task
from app.utils.database import get_db

async def admin_required(current_user: User = Depends(get_current_user)):
    if not bool(current_user.is_admin):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user

async def leader_or_admin_required(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.is_admin:
        return current_user

    user_project_membership = db.query(ProjectMembers).filter(
        ProjectMembers.user_id == current_user.id,
        ProjectMembers.project_id == project_id
    ).first()

    if not user_project_membership:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this project."
        )

    if user_project_membership.role != ProjectMemberRole.LEADER.value:
        raise HTTPException(
            status_code=403,
            detail="You must be an admin or a project leader to add members."
        )

    return current_user

async def can_view_task(
    task_id: int, 
    project_id: int,
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
    if current_user.is_admin:
            return db_task
    
    project_leader = db.query(ProjectMembers).filter(
            ProjectMembers.project_id == project_id,
            ProjectMembers.user_id == current_user.id,
            ProjectMembers.role == ProjectMemberRole.LEADER.value
        ).first()
    if project_leader:
            return db_task
        
    if db_task.assigned_to_user == current_user.id:
            return db_task
        
    raise HTTPException(
        status_code=403,
        detail="Not permitted to view this task"
    )