from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import User 
from app.schemas.user import UserCreate, UserOut, UserUpdate, Token
from app.utils.auth import (
    hash_password, 
    create_access_token, 
    create_refresh_token,
    authenticate_user
)
from app.utils.dependencies import get_db, get_current_active_user
from app.utils.permissions import RoleChecker
from sqlalchemy.orm import Session
from typing import List
from app.utils.storage import StorageService
from app.config import settings
import datetime as dt

router = APIRouter(prefix="/users", tags=["Users"])

# Initialize StorageService with settings
storage = StorageService()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token login"""
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user.last_login = dt.datetime.utcnow()
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    }


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate, 
    current_user: User = Depends(RoleChecker("user:create")),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only) - POST /users"""
    db_user = db.query(User).filter(User.email == user_data.email).first()
    
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    hashed_password = hash_password(user_data.password)
    profile_picture = user_data.profile_picture or settings.default_avatar_url
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        profile_picture=profile_picture,
        bio=user_data.bio,
        timezone=user_data.timezone or "UTC"
    )
    db.add(new_user)
    db.flush()
    db.refresh(new_user)
    return new_user


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile - GET /users/me"""
    return current_user


@router.get("", response_model=List[UserOut])
async def list_users(
    current_user: User = Depends(RoleChecker("user:list")),
    db: Session = Depends(get_db)
):
    """Get all users (admin only) - GET /users"""
    all_users = db.query(User).filter(User.is_deleted == False).all()
    return all_users


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    current_user: User = Depends(RoleChecker("user:list")),
    db: Session = Depends(get_db)
):
    """Get specific user by ID (admin only) - GET /users/{user_id}"""
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    return db_user


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int, 
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker("user:update"))
):
    """Update user (admin only) - PUT /users/{user_id}"""
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    if user_data.username:
        db_user.username = user_data.username
    if user_data.email:
        db_user.email = user_data.email
    if user_data.password:
        db_user.hashed_password = hash_password(user_data.password)
    if user_data.profile_picture is not None:
        db_user.profile_picture = user_data.profile_picture
    if user_data.bio is not None:
        db_user.bio = user_data.bio
    if user_data.timezone is not None:
        db_user.timezone = user_data.timezone

    db.flush()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int, 
    current_user: User = Depends(RoleChecker("user:delete")),
    db: Session = Depends(get_db)
):
    """Soft delete user (admin only) - DELETE /users/{user_id}"""
    db_user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    db_user.is_deleted = True
    db_user.deleted_at = dt.datetime.utcnow()
    db_user.deleted_by = current_user.id
    db.flush()
    
    return None


@router.patch("/me/profile-picture", response_model=UserOut)
async def update_current_user_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """Update current user's profile picture - PATCH /users/me/profile-picture"""
    try:
        content = await file.read()
        filename = file.filename or f"profile_pic_{current_user.id}"
        content_type = file.content_type or "image/jpeg"
        
        upload_result = await storage.upload_file(
            file_content=content,
            filename=filename,
            content_type=content_type,
            user_id=current_user.id
        )
        
        current_user.profile_picture = upload_result["url"]
        db.flush()
        db.refresh(current_user)
        
        return current_user
    
    finally:
        await file.close()
