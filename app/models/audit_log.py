from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.utils.database import Base


class AuditLog(Base):
    """
    Central audit log for tracking all changes across the system.
    Provides AI memory foundation by recording who, what, when, and how data changed.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Who made the change
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    username = Column(String, nullable=True)  # Denormalized for historical tracking
    
    # What was changed
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(Integer, nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)  # INSERT, UPDATE, DELETE, SOFT_DELETE
    
    # Change details
    field_name = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    
    # When it happened
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    # Additional context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(255), nullable=True)
    endpoint = Column(String(255), nullable=True)
