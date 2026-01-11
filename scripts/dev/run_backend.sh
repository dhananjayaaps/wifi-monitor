#!/bin/bash
# Run backend in development mode
cd backend
source venv/bin/activate
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
