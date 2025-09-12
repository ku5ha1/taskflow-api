from app.models.user import User 
from pydantic import BaseModel, EmailStr
import datetime as dt

class UserBase(BaseModel):
    username: str 
    email: EmailStr
    
class UserCreate(UserBase):
    password: str 
    
class UserOut(UserBase):
    id: int
    created_at: dt.datetime
    updated_at: dt.datetime
    
    class Config:
        from_attributes = True
        
class UserInDB(UserOut):
    hashed_password: str
    
class UserLogin(BaseModel):
    username: str 
    password: str