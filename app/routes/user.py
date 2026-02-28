from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from app.models.user import User 
from app.schemas.user import UserCreate, UserOut, UserLogin, UserUpdate
from app.utils.auth import hash_password, create_access_token, get_current_user, verify_password
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

@router.post("/create", response_model=UserOut)
async def create_user(
    user_data: UserCreate, 
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(
        User.email == user_data.email
    ).first()
    if db_user:
        raise HTTPException(
            status_code=409,
            detail=f"Email already registered"
        )
    hashed_password = hash_password(user_data.password)
    profile_picture = user_data.profile_picture or settings.default_avatar_url
    try:
        new_user = User(
            username = user_data.username,
            email = user_data.email,
            hashed_password = hashed_password,
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
            status_code=500,
            detail="Could not add user"
        )
        
@router.put("/update/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int, 
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=404,
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
            status_code=500,
            detail="Could not update user"
        )
        
@router.delete("/delete/{user_id}")
async def delete_user(
    user_id: int, 
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user_id} not found"
        )
    try:
        db.delete(db_user)
        db.commit()
        return {"message": "User deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not delete user"
        )

@router.post("/login")
async def user_login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()

    if db_user is None or not verify_password(user.password, str(db_user.hashed_password)):
        raise HTTPException(    
            status_code=401,
            detail="Invalid Username or Password"
        )

    access_token = create_access_token({"sub": str(db_user.id)})
    db_user.last_login = dt.datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "message": "Login Successful",
        "user": {
            "username": db_user.username,
            "email": db_user.email 
        } 
    }

@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me/update-profile-picture", response_model=UserOut)
async def update_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
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
            status_code=500,
            detail=f"Failed to update profile picture: {str(e)}"
        )
    finally:
        await file.close()

@router.get("/all", response_model=List[UserOut])
async def get_all_users(
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    all_users = db.query(User).all()
    return all_users
