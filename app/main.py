from fastapi import FastAPI
from app.utils.database import Base, engine
from app.utils.minio_init import init_minio_buckets
from app.utils.init_admin import create_super_admin
from app.routes.user import router as user_router
from app.routes.projects import router as project_router
from app.routes.tasks import router as task_router
from app.routes.health import router as health_router
from app.middleware.transaction import TransactionMiddleware

app = FastAPI(
    title="TaskFlow API",
    description="Task Management API with AI features",
    version="2.0.0"
)

# Add transaction middleware for automatic session management
app.add_middleware(TransactionMiddleware)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(user_router)
app.include_router(project_router)
app.include_router(task_router)
app.include_router(health_router)

@app.get("/health")
async def get_health():
    """Health check endpoint"""
    return {"message": "API running successfully", "version": "2.0.0"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    init_db()
    init_minio_buckets()
    create_super_admin()
