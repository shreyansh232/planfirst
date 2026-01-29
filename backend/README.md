# Plandrift Backend

FastAPI backend for the Plandrift travel planning application.

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Python**: 3.12+ (managed by `uv`)
- **ORM**: SQLAlchemy 2.0 (Async)
- **Migrations**: Alembic
- **Validation**: Pydantic V2
- **Auth**: JWT (jose) + Passlib (bcrypt)
- **Database**: PostgreSQL (Dockerized)

## 🚀 Development Setup

### 1. Environment Variables
Create a `.env` file in this directory (or symlink to the root `.env`):

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/plandrift
SECRET_KEY=your-random-secret-key
ALGORITHM=HS256
OPENAI_API_KEY=sk-...
FRONTEND_URL=http://localhost:3000
```

### 2. Install Dependencies
```bash
uv sync
```

### 3. Run Migrations
Ensure your Docker container is running first.
```bash
uv run alembic upgrade head
```

### 4. Start the Server
```bash
uv run uvicorn app.main:app --reload --port 8000
```

## 🏗️ Architecture

- `app/api/`: Route handlers and dependencies.
- `app/core/`: Security and configuration logic.
- `app/db/`: Database models, connection, and CRUD layer.
- `app/schemas/`: Pydantic models for request/response validation.
- `app/services/`: Business logic and AI agent integration.

## 🧪 Common Commands

| Command | Description |
|---------|-------------|
| `uv run alembic revision --autogenerate -m "..."` | Create a new migration |
| `uv run alembic upgrade head` | Apply all migrations |
| `uv run pytest` | Run tests (if implemented) |