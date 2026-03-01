import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.utils.database import Base, get_db
from app.config import settings
import os

# Test database URL
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://taskflow:taskflow_dev@localhost:5432/taskflow_test")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client, db_session):
    """Create admin user and return JWT token"""
    from app.models.user import User
    from app.utils.auth import hash_password, create_access_token
    
    admin = User(
        username="admin_test",
        email="admin@test.local",
        hashed_password=hash_password("admin123"),
        is_admin=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    
    return create_access_token(data={"sub": str(admin.id)})


@pytest.fixture
def regular_user_token(client, db_session):
    """Create regular user and return JWT token"""
    from app.models.user import User
    from app.utils.auth import hash_password, create_access_token
    
    user = User(
        username="user_test",
        email="user@test.local",
        hashed_password=hash_password("user123"),
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return create_access_token(data={"sub": str(user.id)})
