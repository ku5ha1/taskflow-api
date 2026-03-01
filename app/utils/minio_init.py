import logging
from app.utils.storage import StorageService

logger = logging.getLogger(__name__)


def init_minio_buckets():
    """Initialize MinIO buckets on application startup"""
    try:
        storage = StorageService()
        storage.ensure_bucket_exists()
        logger.info(f"MinIO bucket initialization completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize MinIO buckets: {e}")
        raise
