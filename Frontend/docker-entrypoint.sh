#!/bin/sh
set -e
cd /app
# Railway: set Variables → API_URL = https://YOUR-BACKEND.up.railway.app (FastAPI service, not this frontend)
python -c "
import os, json
url = os.environ.get('API_URL', 'http://127.0.0.1:8000').strip().rstrip('/')
with open('config.js', 'w', encoding='utf-8') as f:
    f.write('window.RENTAL_API_BASE = ' + json.dumps(url) + ';\n')
"
exec python -m http.server "${PORT:-8080}" --bind 0.0.0.0
