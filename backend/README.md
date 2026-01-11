# Backend (Flask/Django) Structure

This directory holds the Flask REST API service.

Structure:
- app/
  - api/ (routes & controllers)
  - models.py (ORM models)
  - services/ (business logic)
  - schemas/ (request/response validation via Pydantic)
  - tasks/ (Celery tasks placeholder, in-memory broker)
  - config/ (environment-driven settings)
  - wsgi.py (Gunicorn entrypoint)
- migrations/ (database migrations)
- tests/ (unit/integration tests)
- logs/ (app logs)

Quick start (development):
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=app.wsgi:app
flask run --host=0.0.0.0 --port=8000
```

Environment variables (see `config/.env.example` at repo root):
- `DATABASE_URL` (default: sqlite:///../wifi_monitor.db)
- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS`

API base URL: `/api/v1`
