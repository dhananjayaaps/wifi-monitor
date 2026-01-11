"""Usage aggregation services."""
from datetime import datetime
from typing import Optional
from ..models import aggregate_device_usage


def parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return None


def usage_for_device(device_id: int, start: Optional[str], end: Optional[str]) -> dict:
    start_dt = parse_iso(start)
    end_dt = parse_iso(end)
    return aggregate_device_usage(device_id, start=start_dt, end=end_dt)
