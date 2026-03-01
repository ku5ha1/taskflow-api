from sqlalchemy import Column, Boolean, DateTime, Integer
from sqlalchemy.sql import func


class SoftDeleteMixin:
    """
    Mixin to add soft delete functionality to models.
    Allows AI to reason over historical data even after user deletion.
    """
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)  # User ID who deleted


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.
    """
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
