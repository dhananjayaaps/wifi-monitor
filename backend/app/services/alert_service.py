"""Alert management services."""
from typing import List, Optional
from datetime import datetime, timedelta
from ..extensions import db
from ..models import Alert, AlertHistory, Device, aggregate_device_usage


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
        usage_totals = aggregate_device_usage(device_id)
        cap_total = usage_totals.get("total_bytes", 0)
        if cap_total >= device.data_cap:
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

            latest = (
                AlertHistory.query.filter_by(alert_id=data_cap_alert.id)
                .order_by(AlertHistory.triggered_at.desc())
                .first()
            )
            if latest is None or (datetime.utcnow() - latest.triggered_at) > timedelta(hours=1):
                triggered.append(record_alert_trigger(data_cap_alert, device_id, cap_total))

    return triggered


def list_recent_history(
    user_id: int,
    hours: Optional[int] = 24,
    limit: int = 100,
    offset: int = 0,
) -> List[AlertHistory]:
    """Return AlertHistory entries for a user with optional time filter and pagination."""
    query = AlertHistory.query.join(Alert).filter(Alert.user_id == user_id)

    if hours is not None:
        since = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(AlertHistory.triggered_at >= since)

    histories = (
        query.order_by(AlertHistory.triggered_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return histories


def record_detection_alert(
    user_id: int,
    device_id: int,
    alert_type: str,
    value_at_trigger: int,
    cooldown_seconds: int = 300,
) -> Optional[AlertHistory]:
    """Ensure an alert exists for a detection and record it with cooldown."""
    alert = Alert.query.filter_by(
        user_id=user_id,
        device_id=device_id,
        alert_type=alert_type,
    ).first()

    if not alert:
        alert = Alert(
            user_id=user_id,
            device_id=device_id,
            alert_type=alert_type,
            threshold_value=1,
            is_enabled=True,
        )
        db.session.add(alert)
        db.session.commit()

    if cooldown_seconds:
        latest = (
            AlertHistory.query.filter_by(alert_id=alert.id, device_id=device_id)
            .order_by(AlertHistory.triggered_at.desc())
            .first()
        )
        if latest and (datetime.utcnow() - latest.triggered_at).total_seconds() < cooldown_seconds:
            return None

    return record_alert_trigger(alert, device_id, value_at_trigger)


def clear_alert_history(user_id: int) -> int:
    """Delete alert history entries for all alerts owned by the user."""
    alert_ids = [alert.id for alert in Alert.query.filter_by(user_id=user_id).all()]
    if not alert_ids:
        return 0

    deleted = AlertHistory.query.filter(AlertHistory.alert_id.in_(alert_ids)).delete(
        synchronize_session=False
    )
    db.session.commit()
    return deleted
