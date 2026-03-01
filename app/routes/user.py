from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import User 
from app.schemas.user import UserCreate, UserOut, UserUpdate, Token
from app.utils.auth import (
    hash_password, 
    create_access_token, 
    create_refresh_token,
    get_current_user,
    get_current_active_user,
    authenticate_user
)
from app.utils.database import get_db
from sqlalchemy.orm import Session
from app.utils.depedency import admin_required
from typing import List
from app.utils.storage import StorageService
from app.config import settings
import datetime as dt

router = APIRouter(prefix="/users", tags=["User"])

# Initialize StorageService with settings
storage = StorageService()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Update last login
    user.last_login = dt.datetime.utcnow()
    db.commit()
    
    # Create access and refresh tokens
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


@router.post("/create", response_model=UserOut)
async def create_user(
    user_data: UserCreate, 
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    db_user = db.query(User).filter(
        User.email == user_data.email
    ).first()
    
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    hashed_password = hash_password(user_data.password)
    profile_picture = user_data.profile_picture or settings.default_avatar_url
    
    try:
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            profile_picture=profile_picture,
            bio=user_data.bio,
            timezone=user_data.timezone or "UTC"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user"
        )


@router.get("/me", response_model=UserOut)
async def read_current_user(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile"""
    return current_user


@router.put("/update/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int, 
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    """Update user (admin only)"""
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    try:
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

        db.commit()
        db.refresh(db_user)
        return db_user
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update user"
        )


@router.delete("/delete/{user_id}")
async def delete_user(
    user_id: int, 
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    try:
        db.delete(db_user)
        db.commit()
        return {"message": "User deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete user"
        )


@router.patch("/me/update-profile-picture", response_model=UserOut)
async def update_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """Update current user's profile picture"""
    try:
        content = await file.read()
        filename = file.filename or f"profile_pic_{current_user.id}"
        content_type = file.content_type or "image/jpeg"
        
        # Upload to MinIO and store metadata
        upload_result = await storage.upload_file(
            file_content=content,
            filename=filename,
            content_type=content_type,
            user_id=current_user.id
        )
        
        # Store signed URL in user profile
        current_user.profile_picture = upload_result["url"]
        db.commit()
        db.refresh(current_user)
        
        return current_user

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile picture: {str(e)}"
        )
    
    finally:
        await file.close()


@router.get("/all", response_model=List[UserOut])
async def get_all_users(
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    all_users = db.query(User).all()
    return all_users
