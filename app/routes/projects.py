from fastapi import APIRouter, Depends, HTTPException
from app.utils.depedency import admin_required
from app.models.user import User 
from app.models.projects import Project
from app.utils.database import Base, get_db 
from app.schemas.project import ProjectCreate, ProjectOut, ProjectList, ProjectUpdate
from sqlalchemy.orm import Session
from app.models.project_members import ProjectMembers
from app.schemas.project_members import ProjectMemberCreate, ProjectMemberOut, ProjectMemberUpdate, ProjectMemberRole

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
            created_by = current_user.id
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
async def get_all_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return {
        "projectlist": projects
    }
    
@router.get("/{project_id}", response_model=ProjectOut)
async def get_single_project(project_id: int, db: Session = Depends(get_db)):
    db_project = db.query(Project).filter(
        Project.id == project_id
    ).first()
    if not db_project:
        raise HTTPException(
            status_code=403,
            detail=f"Project with {project_id} not found"
        )
    return db_project

@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    project_data: ProjectCreate, 
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
        db_project.name = project_data.name 
        db_project.description = project_data.description 
        
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