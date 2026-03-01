from app.utils.database import Base
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    depends_on_task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    dependency_type = Column(String(20), default="blocks")  # blocks, related_to, subtask_of
    created_at = Column(DateTime, server_default=func.now())

    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on = relationship("Task", foreign_keys=[depends_on_task_id], back_populates="dependents")
