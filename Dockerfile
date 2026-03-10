# Character Generator API
# Multi-stage build for smaller image

# Stage 1: Build the frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm@9.15.0

# Copy package files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY packages/shared/package.json ./packages/shared/
COPY packages/web/package.json ./packages/web/

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source files
COPY packages/shared ./packages/shared
COPY packages/web ./packages/web

# Build shared package first
RUN pnpm --filter @char-gen/shared build

# Build web package
RUN pnpm --filter @char-gen/web build

# Stage 2: Python backend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python application
COPY bpui ./bpui
COPY blueprints ./blueprints
COPY presets ./presets
COPY rules ./rules

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/packages/web/dist ./packages/web/dist

# Create drafts directory
RUN mkdir -p /app/drafts

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the API
CMD ["python", "-m", "uvicorn", "bpui.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
