"""Device routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from ...schemas.device import DeviceCreate, DeviceUpdate
from ...services import device_service
from ...models import DeviceStat
from ...extensions import db


devices_bp = Blueprint("devices", __name__)


def _serialize(device):
    return device.to_dict()


@devices_bp.route("", methods=["GET"], strict_slashes=False)
@jwt_required()
def list_devices():
    user_id = get_jwt_identity()
    devices = device_service.list_devices(owner_id=user_id)
    return jsonify({"status": "success", "data": [_serialize(d) for d in devices]})


@devices_bp.route("", methods=["POST"], strict_slashes=False)
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


@devices_bp.route("/<int:device_id>/cap", methods=["PUT"])
@jwt_required()
def set_device_cap(device_id: int):
    """Set or clear a device data cap (bytes). Send JSON {"data_cap": null} to clear."""
    user_id = get_jwt_identity()
    device = device_service.get_device(owner_id=user_id, device_id=device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404

    payload = request.get_json(silent=True) or {}
    data_cap = payload.get("data_cap", None)
    if data_cap is not None:
        try:
            data_cap = int(data_cap)
            if data_cap < 0:
                raise ValueError()
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "Invalid data_cap value"}), 400

    device.data_cap = data_cap
    db.session.commit()

    return jsonify({"status": "success", "data": _serialize(device)}), 200


@devices_bp.route("/<int:device_id>/stats", methods=["GET"])
@jwt_required()
def get_device_stats(device_id: int):
    """Get usage statistics for a device over a time period."""
    user_id = get_jwt_identity()
    device = device_service.get_device(owner_id=user_id, device_id=device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404
    
    # Get hours parameter (default 24)
    hours = request.args.get('hours', 24, type=int)
    bucket_minutes = request.args.get('bucket_minutes', type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Query device stats
    stats = DeviceStat.query.filter(
        DeviceStat.device_id == device_id,
        DeviceStat.timestamp >= since
    ).order_by(DeviceStat.timestamp.asc()).all()

    if bucket_minutes and bucket_minutes > 0:
        bucket_seconds = bucket_minutes * 60
        buckets = {}
        for stat in stats:
            ts = stat.timestamp
            bucket_epoch = int(ts.timestamp() // bucket_seconds) * bucket_seconds
            bucket_ts = datetime.utcfromtimestamp(bucket_epoch)
            key = bucket_ts.isoformat()
            if key not in buckets:
                buckets[key] = {
                    "timestamp": key,
                    "bytes_uploaded": 0,
                    "bytes_downloaded": 0,
                }
            buckets[key]["bytes_uploaded"] += stat.bytes_uploaded or 0
            buckets[key]["bytes_downloaded"] += stat.bytes_downloaded or 0

        data = [buckets[k] for k in sorted(buckets.keys())]
        return jsonify({
            "status": "success",
            "data": data
        }), 200
    
    return jsonify({
        "status": "success",
        "data": [stat.to_dict() for stat in stats]
    }), 200


@devices_bp.route("/<int:device_id>/stats", methods=["DELETE"])
@jwt_required()
def clear_device_stats(device_id: int):
    """Delete all usage statistics for a device."""
    user_id = get_jwt_identity()
    device = device_service.get_device(owner_id=user_id, device_id=device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404

    deleted = DeviceStat.query.filter(DeviceStat.device_id == device_id).delete(synchronize_session=False)
    db.session.commit()

    return jsonify({"status": "success", "data": {"deleted": deleted}}), 200
