"""Alert routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ...schemas.alert import AlertCreate, AlertUpdate
from ...services import alert_service, device_service


alerts_bp = Blueprint("alerts", __name__)


def _serialize(alert):
    return alert.to_dict()


@alerts_bp.route("/", methods=["GET"])
@jwt_required()
def list_alerts():
    user_id = get_jwt_identity()
    alerts = alert_service.list_alerts(user_id=user_id)
    return jsonify({"status": "success", "data": [_serialize(a) for a in alerts]})


@alerts_bp.route("/", methods=["POST"])
@jwt_required()
def create_alert():
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    data = AlertCreate(**payload)

    if data.device_id:
        device = device_service.get_device(owner_id=user_id, device_id=data.device_id)
        if not device:
            return jsonify({"status": "error", "message": "Device not found"}), 404

    alert = alert_service.create_alert(
        user_id=user_id,
        device_id=data.device_id,
        alert_type=data.alert_type,
        threshold_value=data.threshold_value,
        is_enabled=data.is_enabled,
    )
    return jsonify({"status": "success", "data": _serialize(alert)}), 201


@alerts_bp.route("/<int:alert_id>", methods=["PUT"])
@jwt_required()
def update_alert(alert_id: int):
    user_id = get_jwt_identity()
    alert = alert_service.get_alert(user_id=user_id, alert_id=alert_id)
    if not alert:
        return jsonify({"status": "error", "message": "Alert not found"}), 404

    payload = request.get_json(silent=True) or {}
    data = AlertUpdate(**payload)

    if data.device_id:
        device = device_service.get_device(owner_id=user_id, device_id=data.device_id)
        if not device:
            return jsonify({"status": "error", "message": "Device not found"}), 404

    alert = alert_service.update_alert(alert, **data.dict())
    return jsonify({"status": "success", "data": _serialize(alert)})
