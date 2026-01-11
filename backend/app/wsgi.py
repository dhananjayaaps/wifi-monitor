"""WSGI entrypoint for Gunicorn."""
from . import create_app

app = create_app()
