"""Device routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ...schemas.device import DeviceCreate, DeviceUpdate
from ...services import device_service


devices_bp = Blueprint("devices", __name__)


def _serialize(device):
    return device.to_dict()


@devices_bp.route("/", methods=["GET"])
@jwt_required()
def list_devices():
    user_id = get_jwt_identity()
    devices = device_service.list_devices(owner_id=user_id)
    return jsonify({"status": "success", "data": [_serialize(d) for d in devices]})


@devices_bp.route("/", methods=["POST"])
@jwt_required()
def create_device():
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    data = DeviceCreate(**payload)
    try:
        device = device_service.create_device(owner_id=user_id, **data.dict())
    except device_service.DeviceError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    return jsonify({"status": "success", "data": _serialize(device)}), 201


@devices_bp.route("/<int:device_id>", methods=["GET"])
@jwt_required()
def get_device(device_id: int):
    user_id = get_jwt_identity()
    device = device_service.get_device(owner_id=user_id, device_id=device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404
    return jsonify({"status": "success", "data": _serialize(device)})


@devices_bp.route("/<int:device_id>", methods=["PUT"])
@jwt_required()
def update_device(device_id: int):
    user_id = get_jwt_identity()
    device = device_service.get_device(owner_id=user_id, device_id=device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404
    payload = request.get_json(silent=True) or {}
    data = DeviceUpdate(**payload)
    device = device_service.update_device(device, **data.dict())
    return jsonify({"status": "success", "data": _serialize(device)})


@devices_bp.route("/<int:device_id>", methods=["DELETE"])
@jwt_required()
def delete_device(device_id: int):
    user_id = get_jwt_identity()
    device = device_service.get_device(owner_id=user_id, device_id=device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404
    device_service.delete_device(device)
    return jsonify({"status": "success"}), 204
