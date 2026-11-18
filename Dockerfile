# ==========================================
# STAGE 1: Build React Frontend Assets
# ==========================================
FROM node:22-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
COPY frontend/.browserslistrc ./
COPY frontend/tsconfig*.json ./
COPY frontend/vite.config.ts ./
COPY frontend/tailwind.config.js ./
COPY frontend/postcss.config.js ./
COPY frontend/index.html ./
COPY frontend/src ./src

RUN npm install --frozen-lockfile || npm install
RUN npm run build

# ==========================================
# STAGE 2: Python Backend & Production Server
# ==========================================
FROM python:3.13-slim AS backend-runner

WORKDIR /app

# Set environment defaults for GCP Cloud Run
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    EDGAR_LOCAL_DATA_DIR=/app/output/data \
    EDGAR_CACHE_DIR=/app/output/cache \
    EDGAR_IDENTITY="Value Investing Alpha alpha@example.com"

# Install system dependencies for financial data manipulation & compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source code and output directories
COPY src /app/src
RUN mkdir -p /app/output/data /app/output/cache

# Copy built frontend assets from STAGE 1
COPY --from=frontend-builder /build/dist /app/frontend/dist

# Cloud Run dynamic port binding
EXPOSE 8080

CMD exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8080}
