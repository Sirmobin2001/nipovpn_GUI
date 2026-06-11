"""Connection testing for the NipoVPN server endpoint.

A simple TCP reachability test that measures handshake latency to the
configured ``serverIp:serverPort``. This does not require the core binary to
be running and gives the user quick feedback on whether the server is up.
"""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass


@dataclass
class TestResult:
    ok: bool
    latency_ms: float | None
    message: str


def tcp_check(host: str, port: int, timeout: float = 5.0) -> TestResult:
    """Attempt a TCP connection and measure latency in milliseconds."""
    host = (host or "").strip()
    if not host:
        return TestResult(False, None, "Server IP/host is empty.")
    try:
        port = int(port)
    except (TypeError, ValueError):
        return TestResult(False, None, f"Invalid port: {port!r}")
    if not 0 < port < 65536:
        return TestResult(False, None, f"Port out of range: {port}")

    start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            latency = (time.monotonic() - start) * 1000.0
            return TestResult(
                True,
                latency,
                f"Connected to {host}:{port} in {latency:.0f} ms.",
            )
    except socket.timeout:
        return TestResult(False, None, f"Timed out after {timeout:.0f}s.")
    except OSError as exc:
        return TestResult(False, None, f"Connection failed: {exc}")
