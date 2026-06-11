"""Main application window for the NipoVPN GUI client."""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .config_model import ConfigError, NipoConfig
from .config_page import ConfigForm
from .connection_test import tcp_check
from .theme import COLORS
from .traffic import TrafficMonitor, available_interfaces
from .utils import bundled_core_path, format_bytes, format_duration, format_rate
from .vpn_controller import VpnController, VpnState
from .widgets import Card, StatCard, StatusPill, hline

NAV_ITEMS = ["Dashboard", "Configuration", "Import / Export", "Logs"]


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("root")
        self.setWindowTitle("NipoVPN Client")
        self.resize(1080, 720)
        self.setMinimumSize(900, 600)

        self.settings = QSettings("NipoVPN", "NipoVPN-GUI")
        self.config = NipoConfig()
        self.controller = VpnController(self)
        self.monitor = TrafficMonitor()

        self._build_ui()
        self._wire_controller()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

        self._restore_settings()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_dashboard())
        self.stack.addWidget(self._build_config_page())
        self.stack.addWidget(self._build_import_page())
        self.stack.addWidget(self._build_logs_page())
        layout.addWidget(self.stack, 1)

    def _build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(220)
        lay = QVBoxLayout(side)
        lay.setContentsMargins(16, 22, 16, 16)
        lay.setSpacing(8)

        brand = QLabel("Nipo<span id='a'>VPN</span>")
        brand.setObjectName("brand")
        brand.setText("Nipo<font color='%s'>VPN</font>" % COLORS["accent"])
        lay.addWidget(brand)
        sub = QLabel("Client")
        sub.setObjectName("hint")
        lay.addWidget(sub)
        lay.addSpacing(18)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for index, name in enumerate(NAV_ITEMS):
            btn = QPushButton(name)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, i=index: self.stack.setCurrentIndex(i))
            self.nav_group.addButton(btn, index)
            lay.addWidget(btn)
        self.nav_group.button(0).setChecked(True)

        lay.addStretch(1)
        self.sidebar_status = StatusPill()
        lay.addWidget(self.sidebar_status)
        version = QLabel("v1.0.0")
        version.setObjectName("hint")
        lay.addWidget(version)
        return side

    def _page_header(self, title: str) -> QWidget:
        header = QWidget()
        row = QHBoxLayout(header)
        row.setContentsMargins(0, 0, 0, 0)
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        row.addWidget(label)
        row.addStretch(1)
        return header

    # ---- Dashboard --------------------------------------------------- #
    def _build_dashboard(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(18)

        header = self._page_header("Dashboard")
        self.status_pill = StatusPill()
        header.layout().addWidget(self.status_pill)
        lay.addWidget(header)

        # Connect control
        connect_card = Card()
        connect_row = QHBoxLayout()
        connect_row.setSpacing(20)
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("connect")
        self.connect_btn.setFixedSize(120, 120)
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.clicked.connect(self._toggle_connection)
        connect_row.addWidget(self.connect_btn)

        info_col = QVBoxLayout()
        info_col.setSpacing(6)
        self.server_label = QLabel("Server: not configured")
        self.proxy_label = QLabel("Local proxy: -")
        self.proto_label = QLabel("Protocol: -")
        for lbl in (self.server_label, self.proxy_label, self.proto_label):
            lbl.setObjectName("statLabel")
            info_col.addWidget(lbl)
        connect_row.addLayout(info_col)
        connect_row.addStretch(1)
        connect_card.body().addLayout(connect_row)
        lay.addWidget(connect_card)

        # Stat cards
        stats = QHBoxLayout()
        stats.setSpacing(16)
        self.sent_card = StatCard("Data Sent", accent=COLORS["accent"])
        self.recv_card = StatCard("Data Received", accent=COLORS["success"])
        self.time_card = StatCard("Session Duration", value="00:00:00")
        for card in (self.sent_card, self.recv_card, self.time_card):
            stats.addWidget(card)
        lay.addLayout(stats)

        # Connection test
        test_card = Card("Connection Test")
        test_row = QHBoxLayout()
        self.test_btn = QPushButton("Test server reachability")
        self.test_btn.setObjectName("primary")
        self.test_btn.setCursor(Qt.PointingHandCursor)
        self.test_btn.clicked.connect(self._run_connection_test)
        test_row.addWidget(self.test_btn)
        self.test_result = QLabel("Not tested yet.")
        self.test_result.setObjectName("statLabel")
        test_row.addWidget(self.test_result, 1)
        test_card.body().addLayout(test_row)
        lay.addWidget(test_card)

        lay.addStretch(1)
        return page

    # ---- Configuration ----------------------------------------------- #
    def _build_config_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 12)
        lay.setSpacing(14)

        header = self._page_header("Configuration")
        for text, slot, obj in (
            ("Import core file", self._import_core, ""),
            ("Import config.yaml", self._import_yaml, ""),
            ("Export config.yaml", self._export_yaml, ""),
            ("Apply", self._apply_config, "primary"),
        ):
            btn = QPushButton(text)
            if obj:
                btn.setObjectName(obj)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(slot)
            header.layout().addWidget(btn)
        lay.addWidget(header)

        self.core_label = QLabel("Core binary: not imported")
        self.core_label.setObjectName("hint")
        lay.addWidget(self.core_label)
        lay.addWidget(hline())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        self.form = ConfigForm()
        scroll.setWidget(self.form)
        lay.addWidget(scroll, 1)
        return page

    # ---- Import / Export --------------------------------------------- #
    def _build_import_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)
        lay.addWidget(self._page_header("Import / Export"))

        # Base64 import
        decode_card = Card("Base64 Config Import")
        hint = QLabel(
            "Paste a base64-encoded config (YAML or JSON). The built-in decoder "
            "accepts standard and URL-safe base64 with or without padding."
        )
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        decode_card.add(hint)
        self.b64_input = QPlainTextEdit()
        self.b64_input.setPlaceholderText("Paste base64 config here...")
        self.b64_input.setFixedHeight(130)
        decode_card.add(self.b64_input)
        decode_row = QHBoxLayout()
        decode_btn = QPushButton("Decode & Load")
        decode_btn.setObjectName("primary")
        decode_btn.setCursor(Qt.PointingHandCursor)
        decode_btn.clicked.connect(self._decode_base64)
        decode_row.addWidget(decode_btn)
        self.b64_status = QLabel("")
        self.b64_status.setObjectName("statLabel")
        decode_row.addWidget(self.b64_status, 1)
        decode_card.body().addLayout(decode_row)
        lay.addWidget(decode_card)

        # Base64 export
        export_card = Card("Base64 Config Export")
        export_hint = QLabel(
            "Generate a shareable base64 string from the current configuration."
        )
        export_hint.setObjectName("hint")
        export_card.add(export_hint)
        self.b64_output = QPlainTextEdit()
        self.b64_output.setReadOnly(True)
        self.b64_output.setFixedHeight(130)
        export_card.add(self.b64_output)
        export_row = QHBoxLayout()
        gen_btn = QPushButton("Generate from current config")
        gen_btn.setCursor(Qt.PointingHandCursor)
        gen_btn.clicked.connect(self._encode_base64)
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("primary")
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_base64)
        export_row.addWidget(gen_btn)
        export_row.addWidget(copy_btn)
        export_row.addStretch(1)
        export_card.body().addLayout(export_row)
        lay.addWidget(export_card)

        lay.addStretch(1)
        return page

    # ---- Logs -------------------------------------------------------- #
    def _build_logs_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)

        header = self._page_header("Logs")
        clear_btn = QPushButton("Clear")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(lambda: self.console.clear())
        header.layout().addWidget(clear_btn)

        # Interface selector for traffic accounting
        self.nic_combo = QComboBox()
        self.nic_combo.addItem("All interfaces", userData=None)
        for nic in available_interfaces():
            self.nic_combo.addItem(nic, userData=nic)
        self.nic_combo.currentIndexChanged.connect(self._on_nic_changed)
        header.layout().addWidget(QLabel("Traffic NIC:"))
        header.layout().addWidget(self.nic_combo)
        lay.addWidget(header)

        self.console = QPlainTextEdit()
        self.console.setObjectName("console")
        self.console.setReadOnly(True)
        lay.addWidget(self.console, 1)
        return page

    # ------------------------------------------------------------------ #
    # Controller wiring
    # ------------------------------------------------------------------ #
    def _wire_controller(self) -> None:
        self.controller.log_line.connect(self._append_log)
        self.controller.state_changed.connect(self._on_state_changed)

    def _append_log(self, line: str) -> None:
        self.console.appendPlainText(line)

    def _on_state_changed(self, state: VpnState) -> None:
        color = {
            VpnState.DISCONNECTED: COLORS["text_muted"],
            VpnState.CONNECTING: COLORS["warning"],
            VpnState.CONNECTED: COLORS["success"],
            VpnState.ERROR: COLORS["danger"],
        }[state]
        self.status_pill.set_status(state.value, color)
        self.sidebar_status.set_status(state.value, color)

        connected = state == VpnState.CONNECTED
        self.connect_btn.setText("Disconnect" if connected else "Connect")
        self.connect_btn.setProperty("connected", "true" if connected else "false")
        self.connect_btn.style().unpolish(self.connect_btn)
        self.connect_btn.style().polish(self.connect_btn)

        if connected and not self.monitor.running:
            self.monitor.start()
        if state in (VpnState.DISCONNECTED, VpnState.ERROR):
            self.monitor.stop()

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #
    def _toggle_connection(self) -> None:
        if self.controller.is_running():
            self.controller.stop()
            return
        self._apply_config(silent=True)
        self.controller.set_config(self.config)
        ok, reason = self.controller.start()
        if not ok:
            self.stack.setCurrentIndex(3)
            self.nav_group.button(3).setChecked(True)
            QMessageBox.warning(self, "Cannot connect", reason)

    def _run_connection_test(self) -> None:
        self._apply_config(silent=True)
        host = self.config.agent.serverIp
        port = self.config.agent.serverPort
        self.test_result.setText(f"Testing {host}:{port} ...")
        QGuiApplication.processEvents()
        result = tcp_check(host, port)
        color = COLORS["success"] if result.ok else COLORS["danger"]
        self.test_result.setText(result.message)
        self.test_result.setStyleSheet(f"color: {color};")
        self._append_log(f"[test] {result.message}")

    def _import_core(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select NipoVPN core binary")
        if not path:
            return
        self.controller.set_core_path(path)
        self.core_label.setText(f"Core binary: {path}")
        self.settings.setValue("core_path", path)
        if not os.access(path, os.X_OK):
            self._append_log(f"[gui] Warning: {path} is not executable.")

    def _import_yaml(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import config.yaml", filter="YAML (*.yaml *.yml);;All files (*)"
        )
        if not path:
            return
        try:
            self.config = NipoConfig.from_yaml_file(path)
        except (ConfigError, OSError) as exc:
            QMessageBox.critical(self, "Import failed", str(exc))
            return
        self.form.load(self.config)
        self._refresh_dashboard_info()
        self._append_log(f"[gui] Imported config from {path}")

    def _export_yaml(self) -> None:
        self._apply_config(silent=True)
        path, _ = QFileDialog.getSaveFileName(
            self, "Export config.yaml", "config.yaml",
            filter="YAML (*.yaml *.yml);;All files (*)",
        )
        if not path:
            return
        try:
            self.config.to_yaml_file(path)
        except OSError as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self._append_log(f"[gui] Exported config to {path}")

    def _apply_config(self, silent: bool = False) -> None:
        try:
            self.config = self.form.to_config()
        except Exception as exc:  # noqa: BLE001 - surface to user
            if not silent:
                QMessageBox.critical(self, "Invalid configuration", str(exc))
            return
        self.controller.set_config(self.config)
        self._refresh_dashboard_info()
        self._save_config_setting()
        problems = self.config.validate()
        if problems and not silent:
            QMessageBox.warning(
                self, "Configuration warnings", "\n".join(problems)
            )
        elif not silent:
            self._append_log("[gui] Configuration applied.")

    def _decode_base64(self) -> None:
        text = self.b64_input.toPlainText()
        try:
            self.config = NipoConfig.from_base64(text)
        except ConfigError as exc:
            self.b64_status.setText(str(exc))
            self.b64_status.setStyleSheet(f"color: {COLORS['danger']};")
            return
        self.form.load(self.config)
        self._refresh_dashboard_info()
        self.b64_status.setText("Decoded and loaded into Configuration.")
        self.b64_status.setStyleSheet(f"color: {COLORS['success']};")
        self._append_log("[gui] Loaded config from base64 import.")

    def _encode_base64(self) -> None:
        self._apply_config(silent=True)
        self.b64_output.setPlainText(self.config.to_base64())

    def _copy_base64(self) -> None:
        text = self.b64_output.toPlainText()
        if not text:
            self._encode_base64()
            text = self.b64_output.toPlainText()
        QGuiApplication.clipboard().setText(text)
        self._append_log("[gui] Base64 config copied to clipboard.")

    def _on_nic_changed(self) -> None:
        nic = self.nic_combo.currentData()
        was_running = self.monitor.running
        self.monitor = TrafficMonitor(nic)
        if was_running:
            self.monitor.start()

    # ------------------------------------------------------------------ #
    # Periodic update
    # ------------------------------------------------------------------ #
    def _tick(self) -> None:
        sample = self.monitor.sample()
        self.sent_card.set_value(format_bytes(sample.sent))
        self.sent_card.set_sub(format_rate(sample.sent_rate))
        self.recv_card.set_value(format_bytes(sample.received))
        self.recv_card.set_sub(format_rate(sample.received_rate))
        self.time_card.set_value(format_duration(sample.elapsed))

    def _refresh_dashboard_info(self) -> None:
        ag = self.config.agent
        self.server_label.setText(f"Server: {ag.serverIp}:{ag.serverPort}")
        self.proxy_label.setText(
            f"Local proxy: {ag.listenIp}:{ag.listenPort}"
        )
        self.proto_label.setText(f"Protocol: {self.config.general.protocol}")

    # ------------------------------------------------------------------ #
    # Settings persistence
    # ------------------------------------------------------------------ #
    def _save_config_setting(self) -> None:
        try:
            self.settings.setValue("config_b64", self.config.to_base64())
        except Exception:  # noqa: BLE001
            pass

    def _restore_settings(self) -> None:
        core_path = self.settings.value("core_path", "", str)
        if not core_path:
            core_path = bundled_core_path()
        if core_path:
            self.controller.set_core_path(core_path)
            self.core_label.setText(f"Core binary: {core_path}")

        config_b64 = self.settings.value("config_b64", "", str)
        if config_b64:
            try:
                self.config = NipoConfig.from_base64(config_b64)
            except ConfigError:
                self.config = NipoConfig()
        self.form.load(self.config)
        self.controller.set_config(self.config)
        self._refresh_dashboard_info()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        if self.controller.is_running():
            self.controller.stop()
        super().closeEvent(event)
