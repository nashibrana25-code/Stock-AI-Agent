# Dockerfile for AI Agent
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY shared/ ./shared/
COPY services/ai-agent/ ./services/ai-agent/
COPY services/data-ingestion/ ./services/data-ingestion/
COPY services/recommendation/ ./services/recommendation/

# Run the AI agent
CMD ["python", "services/ai-agent/autonomous_agent.py"]
