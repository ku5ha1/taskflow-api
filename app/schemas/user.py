from app.models.user import User 
from pydantic import BaseModel, EmailStr
import datetime as dt
from typing import Optional

class UserBase(BaseModel):
    username: str 
    email: EmailStr
    
class UserCreate(UserBase):
    password: str 
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = "UTC"
    
class UserOut(UserBase):
    id: int
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None
    last_login: Optional[dt.datetime] = None
    created_at: dt.datetime
    updated_at: Optional[dt.datetime] = None
    
    class Config:
        from_attributes = True
        
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None

    class Config:
        from_attributes = True

        
class UserInDB(UserOut):
    hashed_password: str
    
class UserLogin(BaseModel):
    username: str 
    password: str