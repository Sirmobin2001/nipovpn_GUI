"""Traffic monitoring (data sent / received).

NipoVPN's agent does not create a dedicated tunnel interface, so the GUI
measures throughput from the host network counters via :mod:`psutil`. The
monitor records a baseline when a session starts and reports the delta since
then, which represents the data transferred while the client is connected.

If a specific network interface is provided, only that NIC's counters are
used; otherwise system-wide counters are used.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import psutil


@dataclass
class TrafficSample:
    """A snapshot of cumulative traffic since the session started."""

    sent: int = 0
    received: int = 0
    sent_rate: float = 0.0
    received_rate: float = 0.0
    elapsed: float = 0.0


class TrafficMonitor:
    """Tracks bytes sent/received since :meth:`start` was called."""

    def __init__(self, nic: str | None = None) -> None:
        self._nic = nic
        self._base_sent = 0
        self._base_recv = 0
        self._last_sent = 0
        self._last_recv = 0
        self._start_time = 0.0
        self._last_time = 0.0
        self._running = False

    def _read_counters(self) -> tuple[int, int]:
        if self._nic:
            counters = psutil.net_io_counters(pernic=True).get(self._nic)
            if counters is None:
                # Fall back to system-wide if the NIC disappeared.
                counters = psutil.net_io_counters()
        else:
            counters = psutil.net_io_counters()
        return counters.bytes_sent, counters.bytes_recv

    def start(self) -> None:
        sent, recv = self._read_counters()
        now = time.monotonic()
        self._base_sent = sent
        self._base_recv = recv
        self._last_sent = sent
        self._last_recv = recv
        self._start_time = now
        self._last_time = now
        self._running = True

    def stop(self) -> None:
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def sample(self) -> TrafficSample:
        """Return cumulative + instantaneous traffic since :meth:`start`."""
        if not self._running:
            return TrafficSample()

        sent, recv = self._read_counters()
        now = time.monotonic()
        interval = now - self._last_time

        sent_rate = 0.0
        recv_rate = 0.0
        if interval > 0:
            sent_rate = max(0, sent - self._last_sent) / interval
            recv_rate = max(0, recv - self._last_recv) / interval

        self._last_sent = sent
        self._last_recv = recv
        self._last_time = now

        return TrafficSample(
            sent=max(0, sent - self._base_sent),
            received=max(0, recv - self._base_recv),
            sent_rate=sent_rate,
            received_rate=recv_rate,
            elapsed=now - self._start_time,
        )


def available_interfaces() -> list[str]:
    """Return the names of network interfaces with traffic counters."""
    try:
        return sorted(psutil.net_io_counters(pernic=True).keys())
    except Exception:  # pragma: no cover - platform dependent
        return []
