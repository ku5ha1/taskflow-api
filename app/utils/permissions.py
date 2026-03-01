from typing import Optional, Callable
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.project_members import ProjectMembers
from app.schemas.project_members import ProjectMemberRole
from app.utils.dependencies import get_db
from app.utils.auth import get_current_user


class PermissionDenied(HTTPException):
    """Custom exception for permission denied"""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class PolicyEngine:
    """
    Central policy engine for permission checks.
    Defines all permission rules in one place for easy auditing and AI safety.
    """
    
    @staticmethod
    def is_admin(user: User) -> bool:
        """Check if user is admin"""
        return bool(user.is_admin)
    
    @staticmethod
    def is_project_leader(user: User, project_id: int, db: Session) -> bool:
        """Check if user is leader of specific project"""
        membership = db.query(ProjectMembers).filter(
            ProjectMembers.user_id == user.id,
            ProjectMembers.project_id == project_id,
            ProjectMembers.role == ProjectMemberRole.LEADER.value,
            ProjectMembers.is_deleted == False
        ).first()
        return membership is not None
    
    @staticmethod
    def is_project_member(user: User, project_id: int, db: Session) -> bool:
        """Check if user is member of specific project"""
        membership = db.query(ProjectMembers).filter(
            ProjectMembers.user_id == user.id,
            ProjectMembers.project_id == project_id,
            ProjectMembers.is_deleted == False
        ).first()
        return membership is not None
    
    @staticmethod
    def can_manage_users(user: User) -> bool:
        """Check if user can create/update/delete users"""
        return PolicyEngine.is_admin(user)
    
    @staticmethod
    def can_create_project(user: User) -> bool:
        """Check if user can create projects"""
        return PolicyEngine.is_admin(user)
    
    @staticmethod
    def can_update_project(user: User, project_id: int, db: Session) -> bool:
        """Check if user can update project"""
        return (PolicyEngine.is_admin(user) or 
                PolicyEngine.is_project_leader(user, project_id, db))
    
    @staticmethod
    def can_delete_project(user: User, project_id: int, db: Session) -> bool:
        """Check if user can delete project"""
        return PolicyEngine.is_admin(user)
    
    @staticmethod
    def can_view_project(user: User, project_id: int, db: Session) -> bool:
        """Check if user can view project"""
        return (PolicyEngine.is_admin(user) or 
                PolicyEngine.is_project_member(user, project_id, db))
    
    @staticmethod
    def can_manage_project_members(user: User, project_id: int, db: Session) -> bool:
        """Check if user can add/remove project members"""
        return (PolicyEngine.is_admin(user) or 
                PolicyEngine.is_project_leader(user, project_id, db))
    
    @staticmethod
    def can_create_task(user: User, project_id: int, db: Session) -> bool:
        """Check if user can create tasks in project"""
        return (PolicyEngine.is_admin(user) or 
                PolicyEngine.is_project_leader(user, project_id, db))
    
    @staticmethod
    def can_update_task(user: User, project_id: int, db: Session) -> bool:
        """Check if user can update tasks in project"""
        return (PolicyEngine.is_admin(user) or 
                PolicyEngine.is_project_leader(user, project_id, db) or
                PolicyEngine.is_project_member(user, project_id, db))
    
    @staticmethod
    def can_delete_task(user: User, project_id: int, db: Session) -> bool:
        """Check if user can delete tasks"""
        return (PolicyEngine.is_admin(user) or 
                PolicyEngine.is_project_leader(user, project_id, db))
    
    @staticmethod
    def can_view_task(user: User, project_id: int, db: Session) -> bool:
        """Check if user can view tasks in project"""
        return (PolicyEngine.is_admin(user) or 
                PolicyEngine.is_project_member(user, project_id, db))


class RoleChecker:
    """
    Dependency for declarative permission checking in routes.
    Usage: current_user: User = Depends(RoleChecker("project:create"))
    """
    
    def __init__(self, action: str, resource_id_param: Optional[str] = None):
        """
        Initialize role checker
        
        Args:
            action: Permission action (e.g., "user:create", "project:update", "task:delete")
            resource_id_param: Optional parameter name for resource ID (e.g., "project_id")
        """
        self.action = action
        self.resource_id_param = resource_id_param
    
    async def __call__(
        self,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if user has permission for action"""
        
        # Extract resource ID from path parameters if specified
        resource_id = None
        if self.resource_id_param:
            resource_id = request.path_params.get(self.resource_id_param)
            if resource_id:
                resource_id = int(resource_id)
        
        # Map actions to policy checks
        permission_map = {
            # User permissions
            "user:create": lambda: PolicyEngine.can_manage_users(current_user),
            "user:update": lambda: PolicyEngine.can_manage_users(current_user),
            "user:delete": lambda: PolicyEngine.can_manage_users(current_user),
            "user:list": lambda: PolicyEngine.can_manage_users(current_user),
            
            # Project permissions
            "project:create": lambda: PolicyEngine.can_create_project(current_user),
            "project:update": lambda: PolicyEngine.can_update_project(current_user, resource_id, db),
            "project:delete": lambda: PolicyEngine.can_delete_project(current_user, resource_id, db),
            "project:view": lambda: PolicyEngine.can_view_project(current_user, resource_id, db),
            
            # Project member permissions
            "project:manage_members": lambda: PolicyEngine.can_manage_project_members(current_user, resource_id, db),
            
            # Task permissions
            "task:create": lambda: PolicyEngine.can_create_task(current_user, resource_id, db),
            "task:update": lambda: PolicyEngine.can_update_task(current_user, resource_id, db),
            "task:delete": lambda: PolicyEngine.can_delete_task(current_user, resource_id, db),
            "task:view": lambda: PolicyEngine.can_view_task(current_user, resource_id, db),
        }
        
        # Check permission
        permission_check = permission_map.get(self.action)
        if not permission_check:
            raise PermissionDenied(f"Unknown action: {self.action}")
        
        if not permission_check():
            raise PermissionDenied(
                f"User {current_user.username} does not have permission for action: {self.action}"
            )
        
        return current_user


# Convenience functions for common role checks
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if not PolicyEngine.is_admin(current_user):
        raise PermissionDenied("Admin privileges required")
    return current_user


def require_project_leader(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Require project leader or admin role"""
    if not (PolicyEngine.is_admin(current_user) or 
            PolicyEngine.is_project_leader(current_user, project_id, db)):
        raise PermissionDenied("Project leader or admin privileges required")
    return current_user


def require_project_member(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Require project membership"""
    if not (PolicyEngine.is_admin(current_user) or 
            PolicyEngine.is_project_member(current_user, project_id, db)):
        raise PermissionDenied("Project membership required")
    return current_user
