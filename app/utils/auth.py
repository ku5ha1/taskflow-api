from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models.user import User
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def hash_password(plain_pwd: str) -> str:
    # Truncate password to 72 bytes to comply with bcrypt's limit
    truncated_pwd = plain_pwd.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(truncated_pwd)

def verify_password(plain_pwd: str, hashed_pwd: str) -> bool:
    # Truncate password to 72 bytes to comply with bcrypt's limit
    truncated_pwd = plain_pwd.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(truncated_pwd, hashed_pwd)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )   

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub") if isinstance(payload, dict) else None

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload"
            )
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )
