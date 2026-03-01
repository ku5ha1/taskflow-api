from pydantic import BaseModel, field_validator
import datetime as dt
from typing import Optional, Dict, Any
import re


class UserBase(BaseModel):
    username: str 
    email: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format, allowing .local domains for development"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        # Also allow .local for development
        local_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        
        if not (re.match(email_pattern, v) or re.match(local_pattern, v)):
            raise ValueError('Invalid email format')
        return v.lower()
    

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
    """Legacy login schema (kept for backward compatibility)"""
    username: str 
    password: str


class Token(BaseModel):
    """OAuth2 token response"""
    access_token: str
    refresh_token: str
    token_type: str
    user: Dict[str, Any]


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None
    username: Optional[str] = None
