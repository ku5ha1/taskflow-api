from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.models.user import User
from app.utils.auth import get_current_user


def get_db(request: Request) -> Session:
    """
    Get database session from request state (managed by TransactionMiddleware).
    """
    return request.state.db


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify user is active"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return current_user


def admin_required(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
