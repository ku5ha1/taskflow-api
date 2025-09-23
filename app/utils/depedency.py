from app.utils.auth import get_current_user
from fastapi import Depends, HTTPException 
from app.models.user import User 
from sqlalchemy.orm import Session 
from app.models.project_members import ProjectMembers
from app.schemas.project_members import ProjectMemberRole
from app.utils.database import get_db

async def admin_required(current_user: User = Depends(get_current_user)):
    if not bool(current_user.is_admin):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user

async def leader_required(
    project_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    user_project_membership = db.query(ProjectMembers).filter(
        ProjectMembers.user_id == current_user.id,
        ProjectMembers.project_id == project_id
    ).first()
    if not user_project_membership:
        raise HTTPException(
            status_code=403,
            detail=f"You are not a member of this project"
        )
    if user_project_membership.role != ProjectMemberRole.LEADER.value:
        raise HTTPException(
            status_code=403,
            detail="You are not a project leader in this project"
        )
    return current_user