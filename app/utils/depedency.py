from app.utils.auth import get_current_user
from fastapi import Depends, HTTPException 
from app.models.user import User 
from sqlalchemy.orm import Session 

async def admin_required(current_user: User = Depends(get_current_user)):
    if not bool(current_user.is_admin):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user