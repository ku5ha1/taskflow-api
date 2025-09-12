from fastapi import FastAPI 
from app.utils.database import Base, engine

app = FastAPI() 

def init_db():
    Base.metadata.create_all(bind=engine)

@app.get("/")
async def get_health():
    return {"message": "API running successfully"}

@app.on_event("startup")
async def startup_event():
    init_db()