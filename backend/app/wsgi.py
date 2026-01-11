"""WSGI entrypoint for Gunicorn."""
# Import the application factory from the `app` module where it's defined.
from .app import create_app


app = create_app()
