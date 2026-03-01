"""
RBAC Security Tests
Tests permission boundaries to ensure users can only access authorized resources
"""
import pytest
from app.models.user import User
from app.models.projects import Project
from app.models.project_members import ProjectMembers
from app.schemas.project_members import ProjectMemberRole
from app.utils.auth import hash_password, create_access_token


class TestUserRBAC:
    """Test user management permissions"""
    
    def test_admin_can_create_users(self, client, admin_token):
        response = client.post(
            "/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "newuser",
                "email": "new@test.local",
                "password": "pass123"
            }
        )
        assert response.status_code == 201
    
    def test_regular_user_cannot_create_users(self, client, regular_user_token):
        response = client.post(
            "/users",
            headers={"Authorization": f"Bearer {regular_user_token}"},
            json={
                "username": "newuser",
                "email": "new@test.local",
                "password": "pass123"
            }
        )
        assert response.status_code == 403
    
    def test_admin_can_delete_users(self, client, admin_token, db_session):
        # Create a user to delete
        user = User(username="todelete", email="delete@test.local", hashed_password=hash_password("pass"))
        db_session.add(user)
        db_session.commit()
        
        response = client.delete(
            f"/users/{user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
    
    def test_regular_user_cannot_delete_users(self, client, regular_user_token, db_session):
        user = User(username="todelete", email="delete@test.local", hashed_password=hash_password("pass"))
        db_session.add(user)
        db_session.commit()
        
        response = client.delete(
            f"/users/{user.id}",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403


class TestProjectRBAC:
    """Test project access permissions"""
    
    def test_admin_can_create_projects(self, client, admin_token):
        response = client.post(
            "/projects",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Test Project",
                "description": "Test description"
            }
        )
        assert response.status_code == 201
    
    def test_regular_user_cannot_create_projects(self, client, regular_user_token):
        response = client.post(
            "/projects",
            headers={"Authorization": f"Bearer {regular_user_token}"},
            json={
                "name": "Test Project",
                "description": "Test description"
            }
        )
        assert response.status_code == 403
    
    def test_project_member_can_view_project(self, client, db_session):
        # Create user, project, and membership
        user = User(username="member", email="member@test.local", hashed_password=hash_password("pass"))
        admin = User(username="admin", email="admin@test.local", hashed_password=hash_password("pass"), is_admin=True)
        db_session.add_all([user, admin])
        db_session.commit()
        
        project = Project(name="Test", description="Test", created_by=admin.id)
        db_session.add(project)
        db_session.commit()
        
        membership = ProjectMembers(project_id=project.id, user_id=user.id, role=ProjectMemberRole.MEMBER.value)
        db_session.add(membership)
        db_session.commit()
        
        token = create_access_token(data={"sub": str(user.id)})
        response = client.get(
            f"/projects/{project.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
    
    def test_non_member_cannot_view_project(self, client, db_session):
        # Create user and project (user is NOT a member)
        user = User(username="outsider", email="outsider@test.local", hashed_password=hash_password("pass"))
        admin = User(username="admin", email="admin@test.local", hashed_password=hash_password("pass"), is_admin=True)
        db_session.add_all([user, admin])
        db_session.commit()
        
        project = Project(name="Test", description="Test", created_by=admin.id)
        db_session.add(project)
        db_session.commit()
        
        token = create_access_token(data={"sub": str(user.id)})
        response = client.get(
            f"/projects/{project.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
    
    def test_project_leader_can_update_project(self, client, db_session):
        user = User(username="leader", email="leader@test.local", hashed_password=hash_password("pass"))
        admin = User(username="admin", email="admin@test.local", hashed_password=hash_password("pass"), is_admin=True)
        db_session.add_all([user, admin])
        db_session.commit()
        
        project = Project(name="Test", description="Test", created_by=admin.id)
        db_session.add(project)
        db_session.commit()
        
        membership = ProjectMembers(project_id=project.id, user_id=user.id, role=ProjectMemberRole.LEADER.value)
        db_session.add(membership)
        db_session.commit()
        
        token = create_access_token(data={"sub": str(user.id)})
        response = client.put(
            f"/projects/{project.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated Name"}
        )
        assert response.status_code == 200
    
    def test_project_member_cannot_update_project(self, client, db_session):
        user = User(username="member", email="member@test.local", hashed_password=hash_password("pass"))
        admin = User(username="admin", email="admin@test.local", hashed_password=hash_password("pass"), is_admin=True)
        db_session.add_all([user, admin])
        db_session.commit()
        
        project = Project(name="Test", description="Test", created_by=admin.id)
        db_session.add(project)
        db_session.commit()
        
        membership = ProjectMembers(project_id=project.id, user_id=user.id, role=ProjectMemberRole.MEMBER.value)
        db_session.add(membership)
        db_session.commit()
        
        token = create_access_token(data={"sub": str(user.id)})
        response = client.put(
            f"/projects/{project.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated Name"}
        )
        assert response.status_code == 403


class TestTaskRBAC:
    """Test task access permissions"""
    
    def test_project_leader_can_create_task(self, client, db_session):
        user = User(username="leader", email="leader@test.local", hashed_password=hash_password("pass"))
        admin = User(username="admin", email="admin@test.local", hashed_password=hash_password("pass"), is_admin=True)
        db_session.add_all([user, admin])
        db_session.commit()
        
        project = Project(name="Test", description="Test", created_by=admin.id)
        db_session.add(project)
        db_session.commit()
        
        membership = ProjectMembers(project_id=project.id, user_id=user.id, role=ProjectMemberRole.LEADER.value)
        db_session.add(membership)
        db_session.commit()
        
        token = create_access_token(data={"sub": str(user.id)})
        response = client.post(
            f"/projects/{project.id}/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Test Task",
                "description": "Test",
                "status": "pending",
                "priority": "medium",
                "project_id": project.id
            }
        )
        assert response.status_code == 201
    
    def test_project_member_cannot_create_task(self, client, db_session):
        user = User(username="member", email="member@test.local", hashed_password=hash_password("pass"))
        admin = User(username="admin", email="admin@test.local", hashed_password=hash_password("pass"), is_admin=True)
        db_session.add_all([user, admin])
        db_session.commit()
        
        project = Project(name="Test", description="Test", created_by=admin.id)
        db_session.add(project)
        db_session.commit()
        
        membership = ProjectMembers(project_id=project.id, user_id=user.id, role=ProjectMemberRole.MEMBER.value)
        db_session.add(membership)
        db_session.commit()
        
        token = create_access_token(data={"sub": str(user.id)})
        response = client.post(
            f"/projects/{project.id}/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Test Task",
                "description": "Test",
                "status": "pending",
                "priority": "medium",
                "project_id": project.id
            }
        )
        assert response.status_code == 403
    
    def test_project_member_can_update_task(self, client, db_session):
        from app.models.tasks import Task
        
        user = User(username="member", email="member@test.local", hashed_password=hash_password("pass"))
        admin = User(username="admin", email="admin@test.local", hashed_password=hash_password("pass"), is_admin=True)
        db_session.add_all([user, admin])
        db_session.commit()
        
        project = Project(name="Test", description="Test", created_by=admin.id)
        db_session.add(project)
        db_session.commit()
        
        membership = ProjectMembers(project_id=project.id, user_id=user.id, role=ProjectMemberRole.MEMBER.value)
        db_session.add(membership)
        db_session.commit()
        
        task = Task(name="Test", description="Test", status="pending", priority="medium", project_id=project.id)
        db_session.add(task)
        db_session.commit()
        
        token = create_access_token(data={"sub": str(user.id)})
        response = client.put(
            f"/projects/{project.id}/tasks/{task.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "in_progress"}
        )
        assert response.status_code == 200
