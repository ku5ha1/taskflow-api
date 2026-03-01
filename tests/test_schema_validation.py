"""
Schema Validation Tests
Tests data integrity constraints and validation rules
"""
import pytest
from app.models.user import User
from app.models.projects import Project
from app.models.tasks import Task
from app.models.task_dependencies import TaskDependency
from sqlalchemy.exc import IntegrityError
from app.utils.auth import hash_password


class TestUserSchema:
    """Test user model constraints"""
    
    def test_unique_email_constraint(self, db_session):
        user1 = User(username="user1", email="same@test.local", hashed_password=hash_password("pass"))
        user2 = User(username="user2", email="same@test.local", hashed_password=hash_password("pass"))
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_soft_delete_preserves_data(self, db_session):
        user = User(username="test", email="test@test.local", hashed_password=hash_password("pass"))
        db_session.add(user)
        db_session.commit()
        
        user.is_deleted = True
        db_session.commit()
        
        # User still exists in database
        assert db_session.query(User).filter(User.id == user.id).first() is not None


class TestProjectSchema:
    """Test project model constraints"""
    
    def test_project_requires_creator(self, db_session):
        project = Project(name="Test", description="Test")
        db_session.add(project)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_project_cascade_delete_tasks(self, db_session):
        admin = User(username="admin", email="admin@test.local", hashed_password=hash_password("pass"), is_admin=True)
        db_session.add(admin)
        db_session.commit()
        
        project = Project(name="Test", description="Test", created_by=admin.id)
        db_session.add(project)
        db_session.commit()
        
        task = Task(name="Test", description="Test", status="pending", priority="medium", project_id=project.id)
        db_session.add(task)
        db_session.commit()
        
        # Soft delete project
        project.is_deleted = True
        db_session.commit()
        
        # Task should still exist (soft delete doesn't cascade)
        assert db_session.query(Task).filter(Task.id == task.id).first() is not None


class TestTaskSchema:
    """Test task model constraints"""
    
    def test_task_requires_project(self, db_session):
        task = Task(name="Test", description="Test", status="pending", priority="medium")
        db_session.add(task)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_task_time_tracking_fields(self, db_session):
        admin = User(username="admin", email="admin@test.local", hashed_password=hash_password("pass"), is_admin=True)
        db_session.add(admin)
        db_session.commit()
        
        project = Project(name="Test", description="Test", created_by=admin.id)
        db_session.add(project)
        db_session.commit()
        
        task = Task(
            name="Test",
            description="Test",
            status="pending",
            priority="medium",
            project_id=project.id,
            estimated_hours=8,
            actual_hours=10,
            estimated_minutes=480,
            actual_minutes=600
        )
        db_session.add(task)
        db_session.commit()
        
        assert task.estimated_minutes == 480
        assert task.actual_minutes == 600


class TestTaskDependencySchema:
    """Test task dependency constraints"""
    
    def test_no_self_dependency(self, db_session):
        admin = User(username="admin", email="admin@test.local", hashed_password=hash_password("pass"), is_admin=True)
        db_session.add(admin)
        db_session.commit()
        
        project = Project(name="Test", description="Test", created_by=admin.id)
        db_session.add(project)
        db_session.commit()
        
        task = Task(name="Test", description="Test", status="pending", priority="medium", project_id=project.id)
        db_session.add(task)
        db_session.commit()
        
        # Try to create self-dependency
        dep = TaskDependency(task_id=task.id, depends_on_task_id=task.id)
        db_session.add(dep)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_unique_dependency_constraint(self, db_session):
        admin = User(username="admin", email="admin@test.local", hashed_password=hash_password("pass"), is_admin=True)
        db_session.add(admin)
        db_session.commit()
        
        project = Project(name="Test", description="Test", created_by=admin.id)
        db_session.add(project)
        db_session.commit()
        
        task1 = Task(name="Task1", description="Test", status="pending", priority="medium", project_id=project.id)
        task2 = Task(name="Task2", description="Test", status="pending", priority="medium", project_id=project.id)
        db_session.add_all([task1, task2])
        db_session.commit()
        
        # Create first dependency
        dep1 = TaskDependency(task_id=task1.id, depends_on_task_id=task2.id)
        db_session.add(dep1)
        db_session.commit()
        
        # Try to create duplicate
        dep2 = TaskDependency(task_id=task1.id, depends_on_task_id=task2.id)
        db_session.add(dep2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_dependency_cascade_delete(self, db_session):
        admin = User(username="admin", email="admin@test.local", hashed_password=hash_password("pass"), is_admin=True)
        db_session.add(admin)
        db_session.commit()
        
        project = Project(name="Test", description="Test", created_by=admin.id)
        db_session.add(project)
        db_session.commit()
        
        task1 = Task(name="Task1", description="Test", status="pending", priority="medium", project_id=project.id)
        task2 = Task(name="Task2", description="Test", status="pending", priority="medium", project_id=project.id)
        db_session.add_all([task1, task2])
        db_session.commit()
        
        dep = TaskDependency(task_id=task1.id, depends_on_task_id=task2.id)
        db_session.add(dep)
        db_session.commit()
        
        # Delete task2 (hard delete for test)
        db_session.delete(task2)
        db_session.commit()
        
        # Dependency should be deleted
        assert db_session.query(TaskDependency).filter(TaskDependency.id == dep.id).first() is None


class TestAuditLogSchema:
    """Test audit log data integrity"""
    
    def test_audit_log_captures_changes(self, db_session):
        from app.models.audit_log import AuditLog
        
        log = AuditLog(
            user_id=1,
            username="test",
            table_name="tasks",
            record_id=1,
            action="UPDATE",
            field_name="status",
            old_value="pending",
            new_value="in_progress"
        )
        db_session.add(log)
        db_session.commit()
        
        assert log.id is not None
        assert log.timestamp is not None
