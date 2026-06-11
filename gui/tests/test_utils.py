from nipovpn_gui.utils import format_bytes, format_duration, format_rate


def test_format_bytes_units():
    assert format_bytes(0) == "0 B"
    assert format_bytes(512) == "512 B"
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(1536) == "1.50 KB"
    assert format_bytes(1024 * 1024) == "1.00 MB"
    assert format_bytes(1024 ** 3) == "1.00 GB"


def test_format_bytes_negative_clamped():
    assert format_bytes(-5) == "0 B"


def test_format_rate():
    assert format_rate(2048) == "2.00 KB/s"


def test_format_duration():
    assert format_duration(0) == "00:00:00"
    assert format_duration(65) == "00:01:05"
    assert format_duration(3661) == "01:01:01"
    assert format_duration(-10) == "00:00:00"
