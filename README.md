# Plandrift

A constraint-first travel planning CLI and Web agent powered by OpenAI with real-time web search.

Unlike typical travel planners that immediately generate generic itineraries, Plandrift **thinks before planning** by following a strict agentic workflow.

## 🚀 The Multi-Phase Workflow

1.  **Clarification**: Asks exactly 5 targeted questions about season, duration, budget, and comfort level.
2.  **Feasibility Check**: Uses real-time web search to evaluate travel advisories, weather, and conditions for the specific travel period.
3.  **Assumptions**: Makes all planning assumptions explicit (e.g., transport modes, accommodation styles) and requires user confirmation.
4.  **Planning**: Researches current prices and creates a detailed day-by-day itinerary with costs and reasoning.
5.  **Refinement**: Allows adjustments for safety, speed, comfort, or location.

## 🛠️ Tech Stack

-   **Backend**: FastAPI (Python 3.12)
    -   **Database**: PostgreSQL with SQLAlchemy 2.0 & Alembic migrations.
    -   **Auth**: Custom JWT-based Authentication (Backend-managed).
    -   **Security**: Bcrypt password hashing.
-   **Frontend**: Next.js 15+ (App Router), React 19, Tailwind CSS 4.
-   **Infrastructure**: Docker Compose for PostgreSQL.
-   **Package Manager**: `uv` for Python, `npm` for Node.js.

## 📦 Project Structure

```text
plandrift/
├── backend/          # FastAPI application
├── frontend/         # Next.js application
├── src/plandrift/    # Core CLI agent logic
├── gemini.md         # Project patterns & standards
└── docker-compose.yml # Infrastructure (Postgres)
```

## 🚥 Getting Started

### 1. Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv)

### 2. Infrastructure Setup
```bash
docker-compose up -d
```

### 3. Backend Setup
```bash
cd backend
uv sync
# Ensure your .env has DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/plandrift
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

### 4. CLI Usage
```bash
uv run plandrift plan "Mumbai to Iceland"
```

## 📄 License
MIT