# syntax=docker/dockerfile:1

# --- Build the frontend into static files ---
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Backend runtime, serving the built frontend as static files ---
FROM python:3.12-slim AS backend
WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./backend/pyproject.toml
COPY backend/app ./backend/app
COPY backend/migrations ./backend/migrations
COPY backend/alembic.ini ./backend/alembic.ini
RUN python -m pip install --no-cache-dir --editable ./backend

COPY --from=frontend-build /app/frontend/dist ./frontend/dist

WORKDIR /app/backend
EXPOSE 8000

# Data/uploads are expected to be bind-mounted at ./backend/data on the host
# (see docker-compose.yml) so `docker compose down` never touches them.
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
