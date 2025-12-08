from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.utils.database import Base
from sqlalchemy.sql import func

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String(100))
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(30), default="active")
    deadline = Column(DateTime, nullable=True)
    tags = Column(String, nullable=True)  # comma-separated
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    creator = relationship("User", back_populates="projects_created")
    members = relationship("ProjectMembers", back_populates="project", cascade="all, delete-orphan")