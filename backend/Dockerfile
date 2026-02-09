FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps for uv install
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN python -m pip install --no-cache-dir uv

# Install dependencies (cached)
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev

# Add virtualenv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy app code
COPY . /app/

# Expose port (Railway uses $PORT)
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
