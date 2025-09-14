from app.utils.database import Base 
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship

class ProjectMembers(Base):
    __tablename__ = "project_members"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String)
    added_at = Column(DateTime, server_default=func.now())
    
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="memberships")