# Railway / container deploy — API only (FastAPI)
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
# Frontend as static files; API + UI from one Railway service (POST /api/* hits FastAPI, not 501)
COPY Frontend/ ./static/

EXPOSE 8000

# Railway sets PORT; default 8000 for local docker run
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
