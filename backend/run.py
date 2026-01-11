"""Simple run script for local development.

Run this from the `backend` directory with an activated venv:

    python run.py

It imports the application factory and starts Flask's development server.
"""
from app.app import create_app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
