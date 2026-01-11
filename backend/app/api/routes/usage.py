"""Usage routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ...services import device_service, usage_service
from ...schemas.usage import UsageQuery


usage_bp = Blueprint("usage", __name__)


def _device_owned(user_id: int, device_id: int):
    return device_service.get_device(owner_id=user_id, device_id=device_id)


@usage_bp.route("/device/<int:device_id>", methods=["GET"])
@jwt_required()
def usage_for_device(device_id: int):
    user_id = get_jwt_identity()
    device = _device_owned(user_id, device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404

    query = UsageQuery(**request.args)
    usage = usage_service.usage_for_device(device_id=device_id, start=query.start, end=query.end)
    return jsonify({"status": "success", "data": usage})
