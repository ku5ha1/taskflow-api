from fastapi import APIRouter, status
from app.utils.database import check_db_health
from app.utils.redis_client import check_redis_health
from app.utils.storage import check_storage_health
import time

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """System health check endpoint"""
    start_time = time.time()
    
    db_start = time.time()
    db_healthy = await check_db_health()
    db_time = round((time.time() - db_start) * 1000, 2)
    
    redis_start = time.time()
    redis_healthy = await check_redis_health()
    redis_time = round((time.time() - redis_start) * 1000, 2)
    
    storage_start = time.time()
    storage_healthy = await check_storage_health()
    storage_time = round((time.time() - storage_start) * 1000, 2)
    
    checks = {
        "database": {"healthy": db_healthy, "response_time_ms": db_time},
        "redis": {"healthy": redis_healthy, "response_time_ms": redis_time},
        "storage": {"healthy": storage_healthy, "response_time_ms": storage_time},
    }
    
    all_healthy = all(check["healthy"] for check in checks.values())
    total_response_time = round((time.time() - start_time) * 1000, 2)
    
    response = {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "response_time_ms": total_response_time,
    }
    
    if all_healthy:
        return response
    else:
        return status.HTTP_503_SERVICE_UNAVAILABLE, response
