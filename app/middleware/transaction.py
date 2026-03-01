import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.utils.database import SessionLocal
from typing import Optional
import jwt
from app.config import settings

logger = logging.getLogger(__name__)


class TransactionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that manages database transactions for each request.
    
    - Creates a new session at the start of each request
    - Sets user context in session for audit logging
    - Commits on successful response (2xx status codes)
    - Rolls back on errors or non-2xx responses
    - Always closes the session in finally block
    """
    
    def extract_user_from_token(self, request: Request) -> tuple[Optional[int], Optional[str]]:
        """Extract user ID and username from JWT token"""
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None, None
        
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            user_id = payload.get('sub')
            # We'll need to query username separately or add it to token
            return int(user_id) if user_id else None, None
        except:
            return None, None
    
    async def dispatch(self, request: Request, call_next):
        db = SessionLocal()
        request.state.db = db
        
        # Set user context for audit logging
        user_id, username = self.extract_user_from_token(request)
        db.info['user_id'] = user_id
        db.info['username'] = username
        db.info['ip_address'] = request.client.host if request.client else None
        db.info['user_agent'] = request.headers.get('user-agent')
        db.info['endpoint'] = f"{request.method} {request.url.path}"
        
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
