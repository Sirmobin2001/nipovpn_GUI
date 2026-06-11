"""Small, Qt-free helpers shared across the GUI."""

from __future__ import annotations


def format_bytes(num: float) -> str:
    """Human readable byte count, e.g. ``1536`` -> ``1.50 KB``."""
    value = float(num)
    if value < 0:
        value = 0.0
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0 or unit == "TB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} TB"


def format_rate(bytes_per_sec: float) -> str:
    """Human readable transfer rate, e.g. ``2048`` -> ``2.00 KB/s``."""
    return f"{format_bytes(bytes_per_sec)}/s"


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as ``HH:MM:SS``."""
    total = int(max(0, seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
