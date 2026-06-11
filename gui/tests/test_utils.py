import nipovpn_gui.utils as utils

from nipovpn_gui.utils import (
    bundled_core_path,
    bundled_icon_path,
    format_bytes,
    format_duration,
    format_rate,
)


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


def test_bundled_core_path_prefers_packaged_binary(tmp_path, monkeypatch):
    packaged_core = tmp_path / "nipovpn.exe"
    packaged_core.write_text("")
    monkeypatch.setattr("sys._MEIPASS", tmp_path, raising=False)

    assert bundled_core_path() == str(packaged_core)


def test_bundled_icon_path_prefers_packaged_icon(tmp_path, monkeypatch):
    packaged_icon = tmp_path / "assets" / "app.png"
    packaged_icon.parent.mkdir()
    packaged_icon.write_text("")
    monkeypatch.setattr("sys._MEIPASS", tmp_path, raising=False)

    assert bundled_icon_path() == str(packaged_icon)


def test_bundled_icon_path_uses_gui_assets_in_dev(tmp_path, monkeypatch):
    gui_root = tmp_path / "gui"
    packaged_icon = gui_root / "assets" / "app.ico"
    packaged_icon.parent.mkdir(parents=True)
    packaged_icon.write_text("")
    monkeypatch.setattr(utils, "__file__", str(gui_root / "nipovpn_gui" / "utils.py"))

    assert bundled_icon_path() == str(packaged_icon)
