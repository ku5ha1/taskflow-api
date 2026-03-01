import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.utils.database import SessionLocal

logger = logging.getLogger(__name__)


class TransactionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that manages database transactions for each request.
    """
    async def dispatch(self, request: Request, call_next):
        # Skip transaction for non-mutating operations if desired
        # For now, we wrap all requests for consistency
        
        db = SessionLocal()
        request.state.db = db
        
        try:
            response: Response = await call_next(request)
            
            # Commit on successful responses (2xx status codes)
            if 200 <= response.status_code < 300:
                db.commit()
                logger.debug(f"Transaction committed for {request.method} {request.url.path}")
            else:
                db.rollback()
                logger.warning(f"Transaction rolled back for {request.method} {request.url.path} (status: {response.status_code})")
            
            return response
            
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction rolled back due to exception: {e}")
            raise
            
        finally:
            db.close()
