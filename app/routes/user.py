from fastapi import APIRouter, HTTPException, Depends
from app.models.user import User 
from app.schemas.user import UserCreate, UserOut, UserLogin
from app.utils.auth import hash_password, create_access_token, get_current_user, verify_password
from app.utils.database import get_db
from sqlalchemy.orm import Session
from app.utils.depedency import admin_required

router = APIRouter(prefix="/user", tags=["User"])

# @router.post("/register", response_model=UserOut)
# async def user_register(user: UserCreate, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(
#         User.username == user.username or User.email == user.email
#     ).first()
#     if db_user:
#         raise HTTPException(
#             status_code=400,
#             detail="Username or Email already in use"
#         )    
#     hashed_password = hash_password(user.password)
#     new_user = User(
#         username = user.username,
#         email = user.email,
#         hashed_password = hashed_password
#     )
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
    
#     return new_user

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
    try:
        new_user = User(
            username = user_data.username,
            email = user_data.email,
            hashed_password = hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=500,
            detail="Could not add user"
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