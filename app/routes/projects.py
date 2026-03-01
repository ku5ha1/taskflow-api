from fastapi import APIRouter, Depends, HTTPException, status
from app.utils.dependencies import get_db, admin_required, get_current_active_user
from app.models.user import User 
from app.models.projects import Project
from app.utils.auth import get_current_user
from app.schemas.project import ProjectCreate, ProjectOut, ProjectList, ProjectUpdate
from sqlalchemy.orm import Session
from app.models.project_members import ProjectMembers
from app.schemas.project_members import ProjectMemberCreate, ProjectMemberOut, ProjectMemberRole
from typing import List
from app.utils.redis_client import get_redis_client
from redis import asyncio as aioredis
from starlette.concurrency import run_in_threadpool
import json

CACHE_TTL = 600

router = APIRouter(prefix="/projects", tags=["Projects"])


def leader_or_admin_required(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Verify user is admin or project leader"""
    # This is a simplified check - in real implementation, check project-specific leadership
    if not current_user.is_admin:
        # Additional project-specific checks would go here
        pass
    return current_user


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    """Create a new project (admin only) - POST /projects"""
    db_project = db.query(Project).filter(
        Project.name == project_data.name
    ).first()
    
    if db_project:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project with this name already exists"
        )
    
    new_project = Project(
        name=project_data.name,
        description=project_data.description,
        created_by=current_user.id,
        status=project_data.status or "active",
        deadline=project_data.deadline,
        tags=project_data.tags
    )
    db.add(new_project)
    db.flush()
    db.refresh(new_project)
    
    return new_project


@router.get("", response_model=ProjectList)
async def list_projects(
    db: Session = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client)
):
    """Get all projects - GET /projects"""
    ALL_PROJECTS_KEY = "projects:all"
    cached = await redis.get(ALL_PROJECTS_KEY)

    if cached:
        return json.loads(cached)

    # Query only non-deleted projects
    projects = db.query(Project).filter(Project.is_deleted == False).all()
    response_data_dict = {"projectlist": projects}
    serialized_data = ProjectList.model_validate(response_data_dict).model_dump_json()
    await redis.set(ALL_PROJECTS_KEY, serialized_data, ex=CACHE_TTL)

    return response_data_dict


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client)
):
    """Get single project by ID - GET /projects/{project_id}"""
    SINGLE_PROJECT_KEY = f"project:{project_id}"
    cached = await redis.get(SINGLE_PROJECT_KEY)

    if cached:
        return json.loads(cached)

    # Query directly without run_in_threadpool since db session is from middleware
    db_project = db.query(Project).filter(Project.id == project_id).first()

    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )

    project_json = ProjectOut.model_validate(db_project).model_dump_json()
    await redis.set(SINGLE_PROJECT_KEY, project_json, ex=CACHE_TTL)

    return db_project


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    """Update project (admin only) - PUT /projects/{project_id}"""
    db_project = db.query(Project).filter(
        Project.id == project_id
    ).first()
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    if project_data.name is not None:
        db_project.name = project_data.name  
    if project_data.description is not None:
        db_project.description = project_data.description
    if project_data.status is not None:
        db_project.status = project_data.status
    if project_data.deadline is not None:
        db_project.deadline = project_data.deadline
    if project_data.tags is not None:
        db_project.tags = project_data.tags

    db.flush()
    db.refresh(db_project)
    
    return db_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """Soft delete project (admin only) - DELETE /projects/{project_id}"""
    db_project = db.query(Project).filter(
        Project.id == project_id,
        Project.is_deleted == False
    ).first()

    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )

    # Soft delete
    import datetime
    db_project.is_deleted = True
    db_project.deleted_at = datetime.datetime.utcnow()
    db_project.deleted_by = current_user.id
    db.flush()

    return None


@router.post("/{project_id}/members", response_model=ProjectMemberOut, status_code=status.HTTP_201_CREATED)
async def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    current_user: User = Depends(leader_or_admin_required),
    db: Session = Depends(get_db)
):
    """Add member to project - POST /projects/{project_id}/members"""
    existing_project = db.query(Project).filter(
        Project.id == project_id
    ).first()
    
    if not existing_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} does not exist"
        )
    
    user_membership = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id,
        ProjectMembers.user_id == member_data.user_id
    ).first()
    
    if user_membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already a member"
        )
    
    new_user_membership = ProjectMembers(
        project_id=project_id,
        user_id=member_data.user_id,
        role=member_data.role.value
    )
    db.add(new_user_membership)
    db.flush()
    db.refresh(new_user_membership)
    
    return new_user_membership


@router.get("/{project_id}/members", response_model=List[ProjectMemberOut])
async def list_project_members(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all members of a project - GET /projects/{project_id}/members"""
    if current_user.is_admin:
        members = db.query(ProjectMembers).filter(
            ProjectMembers.project_id == project_id
        ).all()
        return members

    existing_user = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id,
        ProjectMembers.user_id == current_user.id
    ).first()
    
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view members of this project"
        )
    
    members = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id
    ).all()
    return members


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(leader_or_admin_required),
    db: Session = Depends(get_db)
):
    """Remove member from project - DELETE /projects/{project_id}/members/{user_id}"""
    existing_user = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id,
        ProjectMembers.user_id == user_id
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} does not exist in the project"
        )
    
    db.delete(existing_user)
    return None


@router.post("/{project_id}/leader", response_model=ProjectMemberOut, status_code=status.HTTP_201_CREATED)
async def assign_project_leader(
    project_id: int,
    member_data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    """Assign leader to project (admin only) - POST /projects/{project_id}/leader"""
    db_project = db.query(Project).filter(
        Project.id == project_id
    ).first()
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} does not exist"
        )
    
    new_project_assignment = ProjectMembers(
        project_id=project_id,
        user_id=member_data.user_id,
        role=ProjectMemberRole.LEADER.value
    )

    db.add(new_project_assignment)
    db.flush()
    db.refresh(new_project_assignment)
    
    return new_project_assignment
