"""Usage-related schemas."""
from typing import Optional
from pydantic import BaseModel


class UsageQuery(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None


class UsageResponse(BaseModel):
    device_id: int
    bytes_uploaded: int
    bytes_downloaded: int
    total_bytes: int

    class Config:
        orm_mode = True
