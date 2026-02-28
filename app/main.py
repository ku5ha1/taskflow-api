from fastapi import FastAPI
from app.utils.database import Base, engine
from app.utils.minio_init import init_minio_buckets
from app.utils.init_admin import create_super_admin
from app.routes.user import router as user_router
from app.routes.projects import router as project_router
from app.routes.tasks import router as task_router
from app.routes.health import router as health_router

app = FastAPI()

def init_db():
    Base.metadata.create_all(bind=engine)

app.include_router(user_router)
app.include_router(project_router)
app.include_router(task_router)
app.include_router(health_router)

@app.get("/health")
async def get_health():
    return {"message": "API running successfully"}

@app.on_event("startup")
async def startup_event():
    init_db()
    init_minio_buckets()
    create_super_admin()
