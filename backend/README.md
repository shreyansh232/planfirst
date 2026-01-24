# Plandrift Backend

FastAPI backend for the Plandrift travel planning application.

## Setup

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload --port 8000
```

## Environment Variables

Create a `.env` file:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/plandrift
SECRET_KEY=your-super-secret-key
OPENAI_API_KEY=your-openai-api-key
FRONTEND_URL=http://localhost:3000
DEBUG=true
```

## Database Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Run migrations
uv run alembic upgrade head
```
