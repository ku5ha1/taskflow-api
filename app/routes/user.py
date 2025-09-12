from fastapi import APIRouter, HTTPException, Depends
from app.models.user import User 
from app.schemas.user import UserCreate, UserOut
from app.utils.database import Base 

router = APIRouter(prefix="user", tags=["User"])