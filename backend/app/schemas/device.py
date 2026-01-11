"""Device-related schemas."""
from typing import Optional
from pydantic import BaseModel, constr


class DeviceCreate(BaseModel):
    mac_address: constr(min_length=3, max_length=64)
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    manufacturer: Optional[str] = None
    device_type: Optional[str] = None


class DeviceUpdate(BaseModel):
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    manufacturer: Optional[str] = None
    device_type: Optional[str] = None
    is_active: Optional[bool] = None


class DeviceResponse(BaseModel):
    id: int
    owner_id: int
    mac_address: str
    ip_address: Optional[str]
    hostname: Optional[str]
    manufacturer: Optional[str]
    device_type: Optional[str]
    first_seen: Optional[str]
    last_seen: Optional[str]
    is_active: bool

    class Config:
        orm_mode = True
