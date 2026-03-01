import logging
from app.utils.database import SessionLocal
from app.models.user import User
from app.utils.auth import hash_password
from app.config import settings

logger = logging.getLogger(__name__)


def create_super_admin():
    """Create super admin user if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if any admin user exists
        existing_admin = db.query(User).filter(User.is_admin == True).first()
        
        if existing_admin:
            logger.info(f"Admin user already exists: {existing_admin.username}")
            return
        
        # Check if user with this email already exists
        existing_user = db.query(User).filter(User.email == settings.admin_email).first()
        if existing_user:
            logger.warning(f"User with email {settings.admin_email} already exists but is not admin")
            return
        
        # Create super admin user
        hashed_password = hash_password(settings.admin_password)
        admin_user = User(
            username=settings.admin_username,
            email=settings.admin_email,
            hashed_password=hashed_password,
            is_admin=True,
            bio="System Administrator",
            timezone="UTC",
            profile_picture=settings.default_avatar_url
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"✓ Super admin user created successfully: {settings.admin_username} ({settings.admin_email})")
        logger.info(f"  Username: {settings.admin_username}")
        logger.info(f"  Email: {settings.admin_email}")
        logger.info(f"  Password: {settings.admin_password}")
        logger.warning("⚠ Please change the default admin password after first login!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create super admin user: {e}")
        raise
    finally:
        db.close()
