# Railway: create a SECOND service, set Root Directory = Frontend
# Build variable: API_URL = your backend URL (e.g. https://xxx.up.railway.app) no trailing slash
FROM python:3.11-alpine

WORKDIR /app

ARG API_URL=http://127.0.0.1:8000
COPY . .
RUN printf "window.RENTAL_API_BASE = '%s';\n" "${API_URL}" > config.js

EXPOSE 8080

CMD sh -c "python -m http.server ${PORT:-8080} --bind 0.0.0.0"
