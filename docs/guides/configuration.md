# Configuration Guide

## Backend Configuration
Edit `backend/app/config/settings.py` or use environment variables:
- `DB_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key

## Pi Agent Configuration
Edit `pi-agent/src/config/settings.yaml`:
- `scan_interval_seconds`: Device scan frequency
- `sync_interval_seconds`: Data sync frequency
- `backend_base_url`: Backend API endpoint

## Environment Variables
Create `.env` files in each component directory with sensitive values.
