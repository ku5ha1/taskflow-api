"""
DEPRECATED: This file is kept for backward compatibility.
Use app.utils.dependencies instead.
"""
from app.utils.dependencies import (
    get_db,
    get_current_active_user,
    admin_required
)

# Re-export for backward compatibility
__all__ = ["get_db", "get_current_active_user", "admin_required"]
