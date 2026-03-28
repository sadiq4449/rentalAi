# Railway: Root Directory = Frontend
# Variables (runtime) → API_URL = https://YOUR-BACKEND-SERVICE.up.railway.app  (no trailing slash)
# Must be the FastAPI backend URL, NOT this frontend URL — or POST will hit Python http.server → 501
FROM python:3.11-alpine

WORKDIR /app

COPY . .
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
