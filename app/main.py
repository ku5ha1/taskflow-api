from fastapi import FastAPI 
from app.utils.database import Base, engine
from app.routes.user import router as user_router

app = FastAPI() 

def init_db():
    Base.metadata.create_all(bind=engine)

app.include_router(user_router)

@app.get("/")
async def get_health():
    return {"message": "API running successfully"}

@app.on_event("startup")
async def startup_event():
    init_db()