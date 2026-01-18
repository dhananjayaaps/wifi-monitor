"""Database models for the backend service."""
from datetime import datetime
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
import secrets
from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Agent(TimestampMixin, db.Model):
    __tablename__ = "agents"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime, nullable=True)

    owner = db.relationship("User", backref="agents", lazy=True)

    @staticmethod
    def generate_api_key() -> str:
        return secrets.token_urlsafe(32)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "is_active": self.is_active,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "created_at": self.created_at.isoformat(),
        }


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    devices = db.relationship("Device", backref="owner", lazy=True)
    alerts = db.relationship("Alert", backref="user", lazy=True)
    notifications = db.relationship("Notification", backref="user", lazy=True)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self) -> dict:
        return {"id": self.id, "email": self.email, "created_at": self.created_at.isoformat()}


class Device(TimestampMixin, db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    mac_address = db.Column(db.String(64), unique=True, nullable=False)
    ip_address = db.Column(db.String(64))
    hostname = db.Column(db.String(255))
    manufacturer = db.Column(db.String(255))
    device_type = db.Column(db.String(128))
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    data_cap = db.Column(db.BigInteger, nullable=True)  # Data cap in bytes

    stats = db.relationship("DeviceStat", backref="device", lazy=True, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "mac_address": self.mac_address,
            "ip_address": self.ip_address,
            "hostname": self.hostname,
            "manufacturer": self.manufacturer,
            "device_type": self.device_type,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "is_active": self.is_active,
            "data_cap": self.data_cap,
        }


class DeviceStat(db.Model):
    __tablename__ = "device_stats"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    bytes_uploaded = db.Column(db.BigInteger, default=0)
    bytes_downloaded = db.Column(db.BigInteger, default=0)

    def to_dict(self) -> dict:
        total = (self.bytes_uploaded or 0) + (self.bytes_downloaded or 0)
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat(),
            "bytes_uploaded": self.bytes_uploaded,
            "bytes_downloaded": self.bytes_downloaded,
            "total_bytes": total,
        }


class Alert(TimestampMixin, db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=True)
    alert_type = db.Column(db.String(64), nullable=False)  # e.g., usage_threshold
    threshold_value = db.Column(db.BigInteger, nullable=False)
    is_enabled = db.Column(db.Boolean, default=True)

    device = db.relationship("Device", lazy=True)
    history = db.relationship("AlertHistory", backref="alert", lazy=True, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "alert_type": self.alert_type,
            "threshold_value": self.threshold_value,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat(),
        }


class AlertHistory(db.Model):
    __tablename__ = "alert_history"

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey("alerts.id"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=True)
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    value_at_trigger = db.Column(db.BigInteger, nullable=False)

    device = db.relationship("Device", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "device_id": self.device_id,
            "triggered_at": self.triggered_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "value_at_trigger": self.value_at_trigger,
        }


class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(64), default="generic")
    is_read = db.Column(db.Boolean, default=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "message": self.message,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }


def aggregate_device_usage(device_id: int, start: Optional[datetime] = None, end: Optional[datetime] = None) -> dict:
    query = db.session.query(
        func.sum(DeviceStat.bytes_uploaded).label("uploaded"),
        func.sum(DeviceStat.bytes_downloaded).label("downloaded"),
    ).filter(DeviceStat.device_id == device_id)

    if start:
        query = query.filter(DeviceStat.timestamp >= start)
    if end:
        query = query.filter(DeviceStat.timestamp <= end)

    result = query.one()
    uploaded = result.uploaded or 0
    downloaded = result.downloaded or 0
    return {
        "device_id": device_id,
        "bytes_uploaded": uploaded,
        "bytes_downloaded": downloaded,
        "total_bytes": uploaded + downloaded,
    }
