"""System and health endpoints."""
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required


system_bp = Blueprint("system", __name__)


@system_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@system_bp.route("/settings", methods=["GET"])
@jwt_required()
def get_settings():
    return jsonify({
        "status": "success",
        "data": {
            "default_device_cap": current_app.config.get("DEFAULT_DEVICE_CAP")
        }
    }), 200


@system_bp.route("/settings", methods=["PUT"])
@jwt_required()
def update_settings():
    payload = request.get_json(silent=True) or {}
    default_cap = payload.get("default_device_cap", None)

    if default_cap is not None:
        try:
            default_cap = int(default_cap)
            if default_cap < 0:
                raise ValueError()
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "Invalid default_device_cap"}), 400

    current_app.config["DEFAULT_DEVICE_CAP"] = default_cap
    return jsonify({
        "status": "success",
        "data": {
            "default_device_cap": current_app.config.get("DEFAULT_DEVICE_CAP")
        }
    }), 200
