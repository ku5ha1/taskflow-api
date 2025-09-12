from app.utils.database import Base 
from sqlalchemy import Column, String, DateTime, Integer 
from sqlalchemy.sql import func 
 
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True) 
    email = Column(String, unique=True)
    hashed_password = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())