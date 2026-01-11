"""Alert management services."""
from typing import List, Optional
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
