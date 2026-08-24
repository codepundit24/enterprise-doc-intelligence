
# Build & Dependencies Compilation
FROM python:3.10-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \ 
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Builder stage ya install step mein:
RUN pip install uv && uv pip install --system -r requirements.txt

# Final Lean Production Image
FROM python:3.10-slim AS runner

WORKDIR /app

#Only install runtime-necessary system liberaries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy system python packages from builder stage
COPY --from=builder /usr/local /usr/local
ENV PATH=/root/.local/bin:$PATH

# Copy backend source code
COPY . .

# FastAPI health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port","8000" ]
