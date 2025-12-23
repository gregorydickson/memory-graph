"""Timezone-safe datetime utilities."""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def parse_datetime(value: str) -> datetime:
    """Parse ISO datetime string, ensuring timezone awareness."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def ensure_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware. Assumes UTC if naive."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
