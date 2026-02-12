# Planfirst

A constraint-first travel planning agent powered by AI with real-time web search. Built for web and extensible for CLI.

Unlike typical travel planners that immediately generate generic itineraries, Planfirst **thinks before planning** by following a strict agentic workflow.

## 🚀 The Multi-Phase Workflow

1.  **Clarification**: Intelligently extracts trip details from your initial message and only asks for what's missing (season, duration, budget, interests, etc.)
2.  **Feasibility Check**: Uses real-time web search to evaluate travel advisories, weather, and conditions for the specific travel period
3.  **Assumptions**: Makes all planning assumptions explicit (e.g., transport modes, accommodation styles) and requires user confirmation
4.  **Planning**: Researches current prices and creates a detailed day-by-day itinerary with:
    - Activities with cost estimates and notes
    - Travel times and costs
    - Accommodation recommendations
    - Daily tips (money-saving hacks, hidden gems, fast routes, must-try food)
    - General trip tips (visa info, SIM cards, cultural etiquette, essential apps)
    - Complete budget breakdown
5.  **Refinement**: Allows adjustments for safety, speed, comfort, or location preferences

## 🛠️ Tech Stack

### Backend
-   **Framework**: FastAPI (Python 3.12+)
-   **Database**: PostgreSQL with SQLAlchemy 2.0 (Async) & Alembic migrations
-   **Auth**: 
    - JWT-based authentication with refresh tokens
    - Google OAuth 2.0 integration
    - Bcrypt password hashing
    - Multi-device session management
-   **AI/LLM**: OpenRouter API (supports multiple models including Gemini 3 Flash)
-   **Web Search**: DuckDuckGo Search (duckduckgo-search)
-   **Package Manager**: `uv`

### Frontend
-   **Framework**: Next.js 15+ (App Router)
-   **UI Library**: React 19
-   **Styling**: Tailwind CSS 4
-   **Package Manager**: `pnpm`

### Infrastructure
-   **Container**: Docker Compose (PostgreSQL)
-   **Database**: PostgreSQL 15+

## 📦 Project Structure

```text
plandrift/
├── backend/                      # FastAPI application
│   ├── app/
│   │   ├── agent/               # Travel planning agent logic
│   │   │   ├── agent.py         # Main TravelAgent orchestrator
│   │   │   ├── models.py        # Pydantic models for phases
│   │   │   ├── prompts.py       # Phase-specific prompts
│   │   │   ├── tools.py         # Web search & tool execution
│   │   │   ├── sanitizer.py     # Input sanitization (prompt injection defense)
│   │   │   └── openai_client.py # LLM client wrapper
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── auth.py      # Auth endpoints (register, login, OAuth)
│   │   ├── db/
│   │   │   ├── models.py        # SQLAlchemy models (User, Trip, TripVersion, etc.)
│   │   │   ├── crud.py          # Database operations
│   │   │   └── database.py      # DB connection setup
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── services/            # Business logic layer
│   │   ├── core/                # Security & config
│   │   ├── config.py            # App settings
│   │   └── main.py              # FastAPI app entry point
│   ├── alembic/                 # Database migrations
│   └── scripts/                 # Utility scripts
├── frontend/                     # Next.js application
│   └── src/
│       ├── app/                 # App router pages
│       ├── components/          # React components
│       └── lib/                 # Utilities & API client
├── docker-compose.yml           # PostgreSQL container
└── gemini.md                    # Project patterns & standards
```

## 🚥 Getting Started

### 1. Prerequisites
- **Python**: 3.12+
- **Node.js**: 20+
- **Docker & Docker Compose**: For PostgreSQL
- **uv**: Python package manager ([Install uv](https://github.com/astral-sh/uv))
- **pnpm**: Node.js package manager

### 2. Environment Setup

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/plandrift

# Security
SECRET_KEY=your-super-secret-key-here-change-in-production
ALGORITHM=HS256

# OpenRouter API (for LLM)
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# Frontend
FRONTEND_URL=http://localhost:3000
```

### 3. Infrastructure Setup

Start PostgreSQL:
```bash
docker-compose up -d
```

### 4. Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Start the API server
uv run uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Start the dev server
pnpm dev
```

The frontend will be available at http://localhost:3000

## 🧪 Testing the Agent

You can test the agent directly via a script:

```bash
cd backend
uv run python scripts/test_agent.py
```

## 🔐 Authentication

Planfirst supports two authentication methods:

1. **Email/Password**: Traditional registration and login with JWT tokens
2. **Google OAuth**: Sign in with Google account

Both methods issue:
- **Access Token**: Short-lived (15 minutes), used for API requests
- **Refresh Token**: Long-lived (30 days), used to obtain new access tokens

Refresh tokens support:
- Multi-device sessions
- Device tracking (user agent, IP)
- Individual or bulk revocation (logout from one device or all)

## 🏗️ Key Features

### Agent Capabilities
- ✅ Smart clarification (extracts info from initial prompt, asks only what's missing)
- ✅ Real-time web search for current prices, events, advisories
- ✅ Risk assessment for weather, accessibility, health, infrastructure
- ✅ Explicit assumption generation with user confirmation
- ✅ Day-by-day itinerary with activities, costs, tips
- ✅ Budget breakdown (flights, accommodation, transport, meals, activities)
- ✅ Plan refinement (adjust for safety, speed, comfort, location)
- ✅ Prompt injection protection (input sanitization)

### Database Design
- ✅ **User Management**: Users, preferences, refresh tokens
- ✅ **Trip Versioning**: Separate trip identity from planning iterations
- ✅ **JSONB Storage**: Fast iteration with phase-specific data (constraints, risk, assumptions, plan, budget, days)
- ✅ **5-Phase Workflow**: Tracks clarification → feasibility → assumptions → planning → refinement

### Security
- ✅ JWT-based auth with refresh tokens
- ✅ Google OAuth 2.0
- ✅ Password hashing (bcrypt)
- ✅ CORS configuration
- ✅ Session middleware for OAuth state
- ✅ Input sanitization (anti-injection)

## 🔧 Common Commands

### Backend

| Command | Description |
|---------|-------------|
| `uv sync` | Install/update dependencies |
| `uv run alembic revision --autogenerate -m "message"` | Create new migration |
| `uv run alembic upgrade head` | Apply all migrations |
| `uv run alembic downgrade -1` | Rollback last migration |
| `uv run uvicorn app.main:app --reload` | Start dev server |
| `uv run python scripts/test_agent.py` | Test agent directly |

### Frontend

| Command | Description |
|---------|-------------|
| `pnpm install` | Install dependencies |
| `pnpm dev` | Start dev server |
| `pnpm build` | Build for production |
| `pnpm lint` | Run ESLint |

### Infrastructure

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start PostgreSQL |
| `docker-compose down` | Stop PostgreSQL |
| `docker-compose logs -f postgres` | View PostgreSQL logs |
| `docker-compose ps` | Check container status |

## 📚 Documentation

- **Backend README**: [backend/README.md](backend/README.md)
- **Project Standards**: [gemini.md](gemini.md)
- **Agent Documentation**: [AGENTS.md](AGENTS.md)

## 🗺️ Roadmap

- [ ] Frontend UI for chat-based planning
- [ ] Trip history and saved plans
- [ ] User preferences integration
- [ ] Export itineraries (PDF, calendar)
- [ ] Collaborative trip planning
- [ ] Mobile app

## 📄 License

MIT
