from app.utils.database import Base
from sqlalchemy import Column, ForeignKey, String, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.mixins import SoftDeleteMixin


class Task(Base, SoftDeleteMixin):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(50))
    description = Column(String(50))
    status = Column(String(20))
    priority = Column(String(10))
    due_date = Column(DateTime)
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    tags = Column(String, nullable=True)  # comma-separated
    attachments = Column(String, nullable=True)  # comma-separated URLs/paths
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    assigned_to_user = Column(Integer, ForeignKey('project_members.id'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    project = relationship('Project', back_populates='tasks')
    assigned_to = relationship('ProjectMembers', back_populates='tasks')
