FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /build
COPY requirements.txt .

RUN python -m venv /opt/venv && /opt/venv/bin/python -m pip install --upgrade pip setuptools && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV DATABASE_URL="sqlite:////tmp/inventory.db"

WORKDIR /app

# Upgrade OS packages while running as root.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 10001 appgroup && useradd --system --uid 10001 --gid 10001 --home-dir /app appuser

COPY --from=builder /opt/venv /opt/venv
COPY --chown=10001:10001 app/ ./app/

USER 10001:10001

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
