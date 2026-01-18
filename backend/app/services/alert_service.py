"""Alert management services."""
from typing import List, Optional
from datetime import datetime, timedelta
from ..extensions import db
from ..models import Alert, AlertHistory, Device


def list_alerts(user_id: int) -> List[Alert]:
    return Alert.query.filter_by(user_id=user_id).order_by(Alert.created_at.desc()).all()


def get_alert(user_id: int, alert_id: int) -> Optional[Alert]:
    return Alert.query.filter_by(user_id=user_id, id=alert_id).first()


def create_alert(user_id: int, device_id: int, alert_type: str, threshold_value: int, is_enabled: bool) -> Alert:
    alert = Alert(
        user_id=user_id,
        device_id=device_id,
        alert_type=alert_type,
        threshold_value=threshold_value,
        is_enabled=is_enabled,
    )
    db.session.add(alert)
    db.session.commit()
    return alert


def update_alert(alert: Alert, **kwargs) -> Alert:
    for key, value in kwargs.items():
        if value is not None:
            setattr(alert, key, value)
    db.session.commit()
    return alert


def record_alert_trigger(alert: Alert, device_id: int, value: int) -> AlertHistory:
    history = AlertHistory(alert_id=alert.id, device_id=device_id, value_at_trigger=value)
    db.session.add(history)
    db.session.commit()
    return history


def evaluate_usage_alerts(user_id: int, device_id: int, total_bytes: int) -> List[AlertHistory]:
    """Evaluate usage alerts for a device and record triggers when thresholds are exceeded."""
    if total_bytes is None:
        return []

    alerts = Alert.query.filter(
        Alert.user_id == user_id,
        Alert.is_enabled.is_(True),
        (Alert.device_id.is_(None)) | (Alert.device_id == device_id),
    ).all()

    triggered: List[AlertHistory] = []
    for alert in alerts:
        if alert.alert_type == "usage_threshold" and total_bytes >= alert.threshold_value:
            triggered.append(record_alert_trigger(alert, device_id, total_bytes))

    # Also evaluate device-level data cap (if configured on the Device)
    try:
        device = Device.query.get(device_id)
    except Exception:
        device = None

    if device and device.data_cap is not None:
        # If device has a cap and total_bytes exceeds it, ensure there's a data_cap alert and record it
        if total_bytes >= device.data_cap:
            data_cap_alert = Alert.query.filter_by(
                user_id=user_id,
                device_id=device_id,
                alert_type="data_cap",
                threshold_value=device.data_cap,
            ).first()

            if not data_cap_alert:
                data_cap_alert = Alert(
                    user_id=user_id,
                    device_id=device_id,
                    alert_type="data_cap",
                    threshold_value=device.data_cap,
                    is_enabled=True,
                )
                db.session.add(data_cap_alert)
                db.session.commit()

            triggered.append(record_alert_trigger(data_cap_alert, device_id, total_bytes))

    return triggered


def list_recent_history(user_id: int, hours: int = 24) -> List[AlertHistory]:
    """Return AlertHistory entries for a user within the last `hours` hours."""
    since = datetime.utcnow() - timedelta(hours=hours)
    # Join with Alert to ensure history belongs to user's alerts
    histories = (
        AlertHistory.query.join(Alert)
        .filter(Alert.user_id == user_id, AlertHistory.triggered_at >= since)
        .order_by(AlertHistory.triggered_at.desc())
        .all()
    )
    return histories
