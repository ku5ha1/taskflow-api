from fastapi import APIRouter, Depends, HTTPException
from app.utils.depedency import admin_required, leader_or_admin_required
from app.models.user import User 
from app.models.projects import Project
from app.utils.database import get_db 
from app.utils.auth import get_current_user
from app.schemas.project import ProjectCreate, ProjectOut, ProjectList, ProjectUpdate
from sqlalchemy.orm import Session
from app.models.project_members import ProjectMembers
from app.schemas.project_members import ProjectMemberCreate, ProjectMemberOut, ProjectMemberUpdate, ProjectMemberRole
from typing import List
from app.utils.redis_client import get_redis_client
from redis import asyncio as aioredis
from starlette.concurrency import run_in_threadpool
import json

CACHE_TTL = 600

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/create", response_model=ProjectOut)
async def create_project(
    project_data: ProjectCreate, 
    db: Session = Depends(get_db,),
    current_user: User = Depends(admin_required)):
    db_project = db.query(Project).filter(
        Project.name == project_data.name
    ).first()
    if db_project:
        raise HTTPException(
            status_code=403, 
            detail="Project with this name already exists"
        )
    try:
        new_project = Project(
            name = project_data.name,
            description = project_data.description,
            created_by = current_user.id,
            status = project_data.status or "active",
            deadline = project_data.deadline,
            tags = project_data.tags
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        return new_project
    
    except Exception as e:
        db.rollback()
        print(f'Error creating project: {e}')
        raise HTTPException(
            status_code=500,
            detail="Failed to create project"
        )
        
@router.get("/all", response_model=ProjectList)
async def get_all_projects(
    db: Session = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client)
):
    ALL_PROJECTS_KEY = "projects:all"
    cached = await redis.get(ALL_PROJECTS_KEY)
    if cached: 
        return json.loads(cached) 
    def sync_db_call():
        return db.query(Project).all()
        
    projects = await run_in_threadpool(sync_db_call)

    response_data_dict = {"projectlist": projects}
 
    serialized_data = ProjectList.model_validate(response_data_dict).model_dump_json()

    await redis.set(ALL_PROJECTS_KEY, serialized_data, ex=CACHE_TTL)
    return response_data_dict
    
@router.get("/{project_id}", response_model=ProjectOut)
async def get_single_project(
    project_id: int, 
    db: Session = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client)
    ):
    SINGLE_PROJECT_KEY = f"project:{project_id}"
    cached = await redis.get(SINGLE_PROJECT_KEY)
    if cached:
        return json.loads(cached)
    def sync_db_call():
        return db.query(Project).filter(Project.id == project_id).first()
    db_project = await run_in_threadpool(sync_db_call)
    
    if not db_project:
        raise HTTPException(
            status_code=403,
            detail=f"Project with {project_id} not found"
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
    db_project = db.query(Project).filter(
        Project.id == project_id
    ).first()
    if not db_project:
        raise HTTPException(
            status_code=403,
            detail=f"Project with id: {project_id} not found"
        )
    try:
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
        
        db.commit()
        db.refresh(db_project)
        
        return db_project
    
    except Exception as e:
        db.rollback()
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update project"
        )
        
@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    db_project = db.query(Project).filter(
        Project.id == project_id
    ).first()
    if not db_project:
        raise HTTPException(
            status_code=403,
            detail=f"Project with id: {project_id} not found"
        )
    try:
        db.delete(db_project)
        db.commit()
        
        return {
            "message": "Project deleted successfully"
        }
    except Exception as e:
        db.rollback()
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete project"
        )
        
@router.post("/{project_id}/members/assign-leader", response_model=ProjectMemberOut)
async def assign_leader(
    project_id: int,
    member_data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    db_project = db.query(Project).filter(
        Project.id == project_id
    ).first()
    if not db_project:
        raise HTTPException(
            status_code=404,
            detail=f"Project with id: {project_id} does nto exist"
        )
    existing_member = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id,
        ProjectMembers.user_id == member_data.user_id
    ).first()
    try:
        new_project_assignment = ProjectMembers(
            project_id=project_id,
            user_id=member_data.user_id,
            role=ProjectMemberRole.LEADER.value
        )
        
        db.add(new_project_assignment)
        db.commit()
        db.refresh(new_project_assignment)
        
        return new_project_assignment
        
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while assigning the leader."
        )
        
@router.post("/{project_id}/add-member", response_model=ProjectMemberOut)
async def add_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    current_user: User = Depends(leader_or_admin_required),
    db: Session = Depends(get_db)
):
    existing_project = db.query(Project).filter(
        Project.id == project_id
    ).first()
    if not existing_project:
        raise HTTPException(
            status_code=404,
            detail=f"Project id :{project_id} does not exist"
        )
    user_membership = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id,
        ProjectMembers.user_id == member_data.user_id
    ).first()
    if user_membership:
        raise HTTPException(
            status_code=409, 
            detail="User already a member"
        )
    try:
        new_user_membership = ProjectMembers(
        project_id = project_id,
        user_id = member_data.user_id,
        role = member_data.role.value
    )
        db.add(new_user_membership)
        db.commit()
        db.refresh(new_user_membership)
        
        return new_user_membership
        
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while adding a new member."
        )
        
@router.delete("/{project_id}/remove-member/{user_id}")
async def remove_member_from_project(
    project_id: int,
    user_id: int,
    current_user: User = Depends(leader_or_admin_required),
    db: Session = Depends(get_db)
):
    existing_user = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id,
        ProjectMembers.user_id == user_id
    ).first()
    
    if not existing_user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id: {user_id} does not exist in the Project"
        )
    try:
        db.delete(existing_user)
        db.commit()
        
        return {
            "message": "User removed from the project successfully"
        }
        
    except Exception as e:
        db.rollback()
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=500,
            detail="Could not remove member from the project"
        )
        
@router.get("/{project_id}/members", response_model=List[ProjectMemberOut])
async def list_project_members(
    project_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.is_admin: # type: ignore
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
            status_code=403,
            detail="You do not have the permission to view all members of this project"
        )
    members = db.query(ProjectMembers).filter(
        ProjectMembers.project_id == project_id
    ).all()
    return members 