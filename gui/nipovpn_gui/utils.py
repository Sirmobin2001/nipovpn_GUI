"""Small, Qt-free helpers shared across the GUI."""

from __future__ import annotations

from pathlib import Path
import sys


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


def bundled_core_path() -> str:
    """Return a packaged core binary path if one sits next to the GUI."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    candidates = [
        base_path / "nipovpn",
        base_path / "nipovpn.exe",
        base_path / "bin" / "nipovpn",
        base_path / "bin" / "nipovpn.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return ""


def bundled_icon_path() -> str:
    """Return a packaged app icon if one exists next to the GUI."""
    package_root = Path(__file__).resolve().parents[1]
    runtime_root = Path(getattr(sys, "_MEIPASS", package_root))
    candidates = [
        runtime_root / "app.ico",
        runtime_root / "app.png",
        runtime_root / "assets" / "app.ico",
        runtime_root / "assets" / "app.png",
        package_root / "assets" / "app.ico",
        package_root / "assets" / "app.png",
    ]
    assets_dir = runtime_root / "assets"
    if assets_dir.is_dir():
        for extension in ("*.ico", "*.png", "*.svg", "*.jpg", "*.jpeg"):
            candidates.extend(sorted(assets_dir.glob(extension)))
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return ""
