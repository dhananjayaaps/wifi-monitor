"""Blueprint to serve OpenAPI spec and Swagger UI from backend/docs."""
from pathlib import Path
from flask import Blueprint, send_from_directory, current_app

docs_bp = Blueprint("docs", __name__)


def _docs_dir() -> str:
    # backend/app/api/docs.py -> parents[2] == backend
    p = Path(__file__).resolve().parents[2] / "docs"
    return str(p)


@docs_bp.route("/", methods=["GET"])
def swagger_ui():
    return send_from_directory(_docs_dir(), "swagger.html")


@docs_bp.route("/openapi.yaml", methods=["GET"])
def openapi_spec():
    return send_from_directory(_docs_dir(), "openapi.yaml")


@docs_bp.route("/<path:filename>", methods=["GET"])
def docs_static(filename: str):
    return send_from_directory(_docs_dir(), filename)
