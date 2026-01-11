"""System and health endpoints."""
from flask import Blueprint, jsonify


system_bp = Blueprint("system", __name__)


@system_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})
