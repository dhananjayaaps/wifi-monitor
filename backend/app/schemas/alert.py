"""Alert-related schemas."""
from typing import Optional
from pydantic import BaseModel, constr, conint


class AlertCreate(BaseModel):
    device_id: Optional[int] = None
    alert_type: constr(min_length=3)
    threshold_value: conint(gt=0)
    is_enabled: bool = True


class AlertUpdate(BaseModel):
    device_id: Optional[int] = None
    alert_type: Optional[str] = None
    threshold_value: Optional[int] = None
    is_enabled: Optional[bool] = None


class AlertResponse(BaseModel):
    id: int
    user_id: int
    device_id: Optional[int]
    alert_type: str
    threshold_value: int
    is_enabled: bool
    created_at: str

    class Config:
        from_attributes = True
