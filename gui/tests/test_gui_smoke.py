"""Headless smoke tests for the GUI window and config form."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from nipovpn_gui.config_model import NipoConfig  # noqa: E402
from nipovpn_gui.config_page import ConfigForm  # noqa: E402


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication

    instance = QApplication.instance() or QApplication([])
    yield instance


def test_config_form_load_roundtrip(app):
    cfg = NipoConfig()
    cfg.general.token = "roundtrip-token"
    cfg.agent.serverIp = "203.0.113.5"
    cfg.agent.serverPort = 8443
    cfg.general.fakeUrls = ["a.com", "b.com"]

    form = ConfigForm()
    form.load(cfg)
    result = form.to_config()

    assert result.general.token == "roundtrip-token"
    assert result.agent.serverIp == "203.0.113.5"
    assert result.agent.serverPort == 8443
    assert result.general.fakeUrls == ["a.com", "b.com"]


def test_main_window_builds(app):
    from nipovpn_gui.main_window import MainWindow

    window = MainWindow()
    assert window.stack.count() == 4
    window.close()
