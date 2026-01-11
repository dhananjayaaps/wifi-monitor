"""Device management services."""
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Device


class DeviceError(Exception):
    pass


def list_devices(owner_id: int) -> List[Device]:
    return Device.query.filter_by(owner_id=owner_id).order_by(Device.created_at.desc()).all()


def get_device(owner_id: int, device_id: int) -> Optional[Device]:
    return Device.query.filter_by(owner_id=owner_id, id=device_id).first()


def create_device(owner_id: int, **kwargs) -> Device:
    device = Device(owner_id=owner_id, **kwargs)
    db.session.add(device)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DeviceError("Device with this MAC already exists") from exc
    return device


def update_device(device: Device, **kwargs) -> Device:
    for key, value in kwargs.items():
        if value is not None:
            setattr(device, key, value)
    db.session.commit()
    return device


def delete_device(device: Device) -> None:
    db.session.delete(device)
    db.session.commit()
