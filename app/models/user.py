from app.utils.database import Base 
from sqlalchemy import Column, String, DateTime, Integer, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func 
 
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True) 
    email = Column(String, unique=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    profile_picture = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    timezone = Column(String, default="UTC")
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    projects_created = relationship("Project", back_populates="creator")
    memberships = relationship("ProjectMembers", back_populates="user")