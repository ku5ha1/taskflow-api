## TaskFlow API

Backend-only Task & Project Management API built with FastAPI, SQLAlchemy, and PostgreSQL.

### Tech
- FastAPI, Pydantic
- SQLAlchemy, Alembic
- PostgreSQL
- JWT (JOSE), bcrypt

### Setup
1) Python 3.11+
2) Create a `.env` with:

```
DATABASE_URL=postgresql://...
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

3) Install deps:

```
pip install -r requirements.txt
```

4) Initialize DB (run app once or apply migrations), optionally seed:

```
python seed.py
```

5) Run the API:

```
uvicorn app.main:app --reload
```

OpenAPI docs at `/docs`.

### Auth
- Login: `POST /users/login` → returns `access_token`
- Use: `Authorization: Bearer <token>`

### Endpoints (minimal)

- Health
  - GET `/health`

- Users (`/users`)
  - POST `/users/create` (admin)
  - PUT `/users/update/{user_id}` (admin)
  - DELETE `/users/delete/{user_id}` (admin)
  - POST `/users/login`
  - GET `/users/me` (auth)
  - GET `/users/all` (admin)

- Projects (`/projects`)
  - POST `/projects/create` (admin)
  - GET `/projects/all`
  - GET `/projects/{project_id}`
  - PUT `/projects/{project_id}` (admin)
  - DELETE `/projects/{project_id}` (admin)
  - GET `/projects/{project_id}/members` (auth)
  - DELETE `/projects/{project_id}/remove-member/{user_id}` (leader/admin)
  - Member management (if present): assign leader / add member

- Tasks (`/projects/{project_id}/tasks`)
  - POST `/create` (leader/admin)
  - PUT `/update/{task_id}` (auth)
  - PATCH `/{task_id}/status` (assignee)
  - GET `/{task_id}` (admin/leader/assignee)
  - GET `/` (filters: `status, priority, assigned_to, due_before, due_after, limit, offset`)
  - DELETE `/delete/{task_id}` (leader/admin)

### Notes
- Seed users: admin / alice / bob (see `seed.py`)
- Health check and Swagger available when server is running.
