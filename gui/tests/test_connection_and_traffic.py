import socket
import threading

from nipovpn_gui.connection_test import tcp_check
from nipovpn_gui.traffic import TrafficMonitor, TrafficSample


def _start_server() -> tuple[str, int, socket.socket]:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    host, port = srv.getsockname()

    def _accept():
        try:
            conn, _ = srv.accept()
            conn.close()
        except OSError:
            pass

    threading.Thread(target=_accept, daemon=True).start()
    return host, port, srv


def test_tcp_success():
    host, port, srv = _start_server()
    try:
        result = tcp_check(host, port, timeout=2.0)
        assert result.ok
        assert result.latency_ms is not None
    finally:
        srv.close()


def test_tcp_refused():
    # Port 1 is almost always closed for a normal user.
    result = tcp_check("127.0.0.1", 1, timeout=1.0)
    assert not result.ok


def test_tcp_empty_host():
    result = tcp_check("", 80)
    assert not result.ok
    assert "empty" in result.message.lower()


def test_tcp_invalid_port():
    result = tcp_check("127.0.0.1", 99999)
    assert not result.ok


def test_traffic_monitor_initial_state():
    monitor = TrafficMonitor()
    assert not monitor.running
    assert monitor.sample() == TrafficSample()


def test_traffic_monitor_runs():
    monitor = TrafficMonitor()
    monitor.start()
    assert monitor.running
    sample = monitor.sample()
    assert sample.sent >= 0
    assert sample.received >= 0
    assert sample.elapsed >= 0
    monitor.stop()
    assert not monitor.running
