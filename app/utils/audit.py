from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from typing import Optional
import json


class AuditService:
    """Service for managing audit logs"""
    
    # Tables to audit (exclude audit_logs itself)
    AUDITED_TABLES = {'users', 'projects', 'tasks', 'project_members', 'file_metadata'}
    
    @staticmethod
    def get_current_user_info(session: Session) -> tuple[Optional[int], Optional[str]]:
        """
        Get current user info from session.info (set by middleware/dependency)
        Returns: (user_id, username)
        """
        if hasattr(session, 'info'):
            return session.info.get('user_id'), session.info.get('username')
        return None, None
    
    @staticmethod
    def get_request_context(session: Session) -> dict:
        """Get request context (IP, user agent, endpoint) from session.info"""
        if hasattr(session, 'info'):
            return {
                'ip_address': session.info.get('ip_address'),
                'user_agent': session.info.get('user_agent'),
                'endpoint': session.info.get('endpoint')
            }
        return {'ip_address': None, 'user_agent': None, 'endpoint': None}
    
    @staticmethod
    def create_audit_log(
        session: Session,
        table_name: str,
        record_id: int,
        action: str,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None
    ):
        """Create an audit log entry"""
        user_id, username = AuditService.get_current_user_info(session)
        context = AuditService.get_request_context(session)
        
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            table_name=table_name,
            record_id=record_id,
            action=action,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            **context
        )
        
        session.add(audit_log)
    
    @staticmethod
    def serialize_value(value) -> Optional[str]:
        """Serialize a value to string for audit log"""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        try:
            return json.dumps(value, default=str)
        except:
            return str(value)


def setup_audit_listeners(Base):
    """
    Setup SQLAlchemy event listeners for automatic audit logging.
    Call this once during application startup.
    """
    
    @event.listens_for(Session, 'before_flush')
    def before_flush(session, flush_context, instances):
        """Track changes before flush"""
        
        # Track new objects (INSERT)
        for obj in session.new:
            table_name = obj.__tablename__
            if table_name not in AuditService.AUDITED_TABLES:
                continue
            
            # We'll log INSERT after flush when we have the ID
            if not hasattr(session, '_audit_inserts'):
                session._audit_inserts = []
            session._audit_inserts.append(obj)
        
        # Track modified objects (UPDATE)
        for obj in session.dirty:
            table_name = obj.__tablename__
            if table_name not in AuditService.AUDITED_TABLES:
                continue
            
            state = inspect(obj)
            changes = {}
            
            for attr in state.attrs:
                hist = attr.load_history()
                if hist.has_changes():
                    old_value = hist.deleted[0] if hist.deleted else None
                    new_value = hist.added[0] if hist.added else None
                    changes[attr.key] = (old_value, new_value)
            
            if changes:
                if not hasattr(session, '_audit_updates'):
                    session._audit_updates = []
                session._audit_updates.append((obj, changes))
        
        # Track deleted objects (DELETE)
        for obj in session.deleted:
            table_name = obj.__tablename__
            if table_name not in AuditService.AUDITED_TABLES:
                continue
            
            if not hasattr(session, '_audit_deletes'):
                session._audit_deletes = []
            session._audit_deletes.append(obj)
    
    @event.listens_for(Session, 'after_flush')
    def after_flush(session, flush_context):
        """Create audit logs after flush (when we have IDs)"""
        
        # Log INSERTs
        if hasattr(session, '_audit_inserts'):
            for obj in session._audit_inserts:
                AuditService.create_audit_log(
                    session=session,
                    table_name=obj.__tablename__,
                    record_id=obj.id,
                    action='INSERT'
                )
            delattr(session, '_audit_inserts')
        
        # Log UPDATEs
        if hasattr(session, '_audit_updates'):
            for obj, changes in session._audit_updates:
                for field_name, (old_value, new_value) in changes.items():
                    # Skip internal SQLAlchemy fields
                    if field_name.startswith('_'):
                        continue
                    
                    AuditService.create_audit_log(
                        session=session,
                        table_name=obj.__tablename__,
                        record_id=obj.id,
                        action='UPDATE',
                        field_name=field_name,
                        old_value=AuditService.serialize_value(old_value),
                        new_value=AuditService.serialize_value(new_value)
                    )
            delattr(session, '_audit_updates')
        
        # Log DELETEs (or SOFT_DELETEs)
        if hasattr(session, '_audit_deletes'):
            for obj in session._audit_deletes:
                # Check if it's a soft delete
                action = 'SOFT_DELETE' if hasattr(obj, 'is_deleted') and obj.is_deleted else 'DELETE'
                
                AuditService.create_audit_log(
                    session=session,
                    table_name=obj.__tablename__,
                    record_id=obj.id,
                    action=action
                )
            delattr(session, '_audit_deletes')
