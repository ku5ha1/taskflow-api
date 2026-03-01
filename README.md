# TaskFlow API

Task and Project Management API built with FastAPI, SQLAlchemy, and PostgreSQL.

## Project Structure

```
taskflow-api/
├── app/
│   ├── models/          # SQLAlchemy models
│   ├── routes/          # API endpoints
│   ├── schemas/         # Pydantic schemas
│   ├── utils/           # Auth, permissions, database
│   ├── middleware/      # Transaction middleware
│   └── main.py          # FastAPI application
├── tests/               # Pytest test suite
├── migrations/          # Database migrations
└── docker-compose.yml   # Container orchestration
```

## Tech Stack

### Backend
- FastAPI - Modern Python web framework
- SQLAlchemy - ORM and database toolkit
- PostgreSQL - Relational database
- Redis - Caching and task queue
- Celery - Distributed task processing

### Storage
- MinIO - S3-compatible object storage

### Authentication
- JWT (PyJWT) - Token-based authentication
- pwdlib[argon2] - Password hashing

### Testing
- Pytest - Testing framework
- pytest-cov - Coverage reporting

### Code Quality
- Black - Code formatting
- Flake8 - Linting
- isort - Import sorting
- MyPy - Type checking

## Setup

### Prerequisites
- Python 3.11+
- Docker and Docker Compose

### Installation

1. Clone the repository
```bash
git clone https://github.com/ku5ha1/taskflow-api.git
cd taskflow-api
```

2. Create environment file
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start services with Docker Compose
```bash
docker-compose up -d
```

4. Access the API
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

### Local Development (without Docker)

1. Install dependencies
```bash
pip install -r requirements.txt
```

2. Configure database connection in `.env`

3. Run the application
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication
- POST `/users/login` - Login and receive JWT token
- Use header: `Authorization: Bearer <token>`

### Health Check
- GET `/health` - Service health status

### Users
- POST `/users` - Create user (admin only)
- GET `/users/me` - Get current user profile
- GET `/users` - List all users (admin only)
- GET `/users/{user_id}` - Get user by ID (admin only)
- PUT `/users/{user_id}` - Update user (admin only)
- DELETE `/users/{user_id}` - Soft delete user (admin only)

### Projects
- POST `/projects` - Create project (admin only)
- GET `/projects` - List all projects
- GET `/projects/{project_id}` - Get project details
- PUT `/projects/{project_id}` - Update project (admin/leader)
- DELETE `/projects/{project_id}` - Soft delete project (admin only)
- POST `/projects/{project_id}/members` - Add member (admin/leader)
- GET `/projects/{project_id}/members` - List project members
- DELETE `/projects/{project_id}/members/{user_id}` - Remove member (admin/leader)

### Tasks
- POST `/projects/{project_id}/tasks` - Create task (admin/leader)
- GET `/projects/{project_id}/tasks` - List tasks with filters
- GET `/projects/{project_id}/tasks/{task_id}` - Get task details
- PUT `/projects/{project_id}/tasks/{task_id}` - Update task (members)
- DELETE `/projects/{project_id}/tasks/{task_id}` - Soft delete task (admin/leader)

Query parameters for task listing:
- `status` - Filter by status
- `priority` - Filter by priority
- `assigned_to` - Filter by assigned user
- `due_before` - Tasks due before date
- `due_after` - Tasks due after date
- `limit` - Pagination limit
- `offset` - Pagination offset

## Features

### Core Functionality
- Role-based access control (Admin, Project Leader, Member)
- Centralized permission system
- Soft delete with audit trail
- Transaction middleware for data consistency
- Task dependency tracking
- Time tracking (estimated vs actual hours/minutes)

### Data Tracking
- Audit logs for all changes (who, what, when, where)
- Soft deletes preserve historical data
- User context tracking (IP, user agent, endpoint)

### Testing
- Comprehensive RBAC security tests
- Schema validation tests
- Automated CI/CD pipeline with GitHub Actions

## Enhancements and Future Scope

### AI Microservice Integration

The backend is designed to support an AI-powered project intelligence layer that will provide:

**Semantic Memory and RAG**
- PGVector integration for hybrid search across tasks and project documentation
- Semantic search capabilities for finding similar tasks and historical context
- Document embedding and retrieval for project knowledge base

**Predictive Analytics**
- Velocity drift detection using estimated vs actual time metrics
- Critical path analysis using task dependency graph
- Anomaly detection for project health monitoring
- Deadline risk forecasting based on historical patterns

**Agentic Orchestration**
- LangGraph-based multi-agent system for project analysis
- Forensic Agent: Analyzes audit logs to identify root causes of delays
- Risk Agent: Traverses dependency graph to forecast bottlenecks
- Workload Agent: Suggests task reassignments based on capacity and skills

**Safety and Observability**
- Zero-trust tool calling with JWT propagation
- Human-in-the-loop approval for AI recommendations
- LangSmith integration for trace observability and performance benchmarking

The current backend provides the foundation with audit logs, dependency tracking, and fine-grained time metrics needed for AI analysis.

