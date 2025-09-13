from fastapi import APIRouter, Depends, HTTPException
from app.utils.depedency import admin_required
from app.models.user import User 
from app.models.projects import Project
from app.utils.database import Base, get_db 
from app.schemas.project import ProjectCreate, ProjectOut, ProjectList, ProjectUpdate
from sqlalchemy.orm import Session

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