"""Manual configuration editor page.

Builds editable form controls for every field in :class:`NipoConfig` and can
read the controls back into a config object (``manual config import``).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .config_model import (
    AgentConfig,
    GeneralConfig,
    LogConfig,
    NipoConfig,
    ServerConfig,
)
from .widgets import Card, field_row


def _spin(maximum: int = 65535) -> QSpinBox:
    box = QSpinBox()
    box.setRange(0, maximum)
    box.setFixedHeight(38)
    return box


def _list_to_text(items: list[str]) -> str:
    return "\n".join(items)


def _text_to_list(text: str) -> list[str]:
    parts: list[str] = []
    for chunk in text.replace(",", "\n").splitlines():
        item = chunk.strip()
        if item:
            parts.append(item)
    return parts


class ConfigForm(QWidget):
    """Editable form for a full NipoVPN configuration."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        # --- General -------------------------------------------------- #
        self.token = QLineEdit()
        self.protocol = QComboBox()
        self.protocol.addItems(["http", "socks5"])
        self.timeout = _spin()
        self.pull_timeout = _spin()
        self.tunnel_enable = QCheckBox("Enable TCP/TLS tunnel mode")
        self.connection_reuse = QCheckBox("Reuse connection per request")
        self.tls_enable = QCheckBox("Enable TLS between agent and server")
        self.tls_verify = QCheckBox("Verify peer certificate")
        self.fake_urls = QPlainTextEdit()
        self.fake_urls.setFixedHeight(90)
        self.methods = QLineEdit()
        self.endpoints = QLineEdit()
        self.tls_cert = QLineEdit()
        self.tls_key = QLineEdit()
        self.tls_ca = QLineEdit()

        general = Card("General")
        g = QGridLayout()
        g.setHorizontalSpacing(14)
        g.setVerticalSpacing(12)
        g.addWidget(field_row("Token", self.token), 0, 0, 1, 2)
        g.addWidget(field_row("Protocol", self.protocol), 1, 0)
        g.addWidget(field_row("Timeout (s)", self.timeout), 1, 1)
        g.addWidget(field_row("Pull timeout (ms)", self.pull_timeout), 2, 0)
        g.addWidget(field_row("Methods (comma separated)", self.methods), 3, 0)
        g.addWidget(field_row("Endpoints (comma separated)", self.endpoints), 3, 1)
        g.addWidget(field_row("Fake URLs (one per line)", self.fake_urls), 4, 0, 1, 2)
        g.addWidget(field_row("TLS cert file", self.tls_cert), 5, 0)
        g.addWidget(field_row("TLS key file", self.tls_key), 5, 1)
        g.addWidget(field_row("TLS CA file", self.tls_ca), 6, 0, 1, 2)
        general.body().addLayout(g)
        for box in (
            self.tunnel_enable,
            self.connection_reuse,
            self.tls_enable,
            self.tls_verify,
        ):
            general.add(box)
        root.addWidget(general)

        # --- Agent (client) ------------------------------------------ #
        self.agent_threads = _spin(4096)
        self.agent_listen_ip = QLineEdit()
        self.agent_listen_port = _spin()
        self.server_ip = QLineEdit()
        self.server_port = _spin()
        self.http_version = QLineEdit()
        self.user_agent = QLineEdit()

        agent = Card("Agent (Client)")
        a = QGridLayout()
        a.setHorizontalSpacing(14)
        a.setVerticalSpacing(12)
        a.addWidget(field_row("Server IP", self.server_ip), 0, 0)
        a.addWidget(field_row("Server port", self.server_port), 0, 1)
        a.addWidget(field_row("Local listen IP", self.agent_listen_ip), 1, 0)
        a.addWidget(field_row("Local listen port", self.agent_listen_port), 1, 1)
        a.addWidget(field_row("Threads", self.agent_threads), 2, 0)
        a.addWidget(field_row("HTTP version", self.http_version), 2, 1)
        a.addWidget(field_row("User agent", self.user_agent), 3, 0, 1, 2)
        agent.body().addLayout(a)
        root.addWidget(agent)

        # --- Server --------------------------------------------------- #
        self.server_threads = _spin(4096)
        self.server_listen_ip = QLineEdit()
        self.server_listen_port = _spin()

        server = Card("Server")
        s = QGridLayout()
        s.setHorizontalSpacing(14)
        s.setVerticalSpacing(12)
        s.addWidget(field_row("Listen IP", self.server_listen_ip), 0, 0)
        s.addWidget(field_row("Listen port", self.server_listen_port), 0, 1)
        s.addWidget(field_row("Threads", self.server_threads), 1, 0)
        server.body().addLayout(s)
        root.addWidget(server)

        # --- Log ------------------------------------------------------ #
        self.log_level = QComboBox()
        self.log_level.addItems(["INFO", "TRACE", "DEBUG"])
        self.log_file = QLineEdit()

        log = Card("Logging")
        log_grid = QGridLayout()
        log_grid.setHorizontalSpacing(14)
        log_grid.addWidget(field_row("Log level", self.log_level), 0, 0)
        log_grid.addWidget(field_row("Log file", self.log_file), 0, 1)
        log.body().addLayout(log_grid)
        root.addWidget(log)
        root.addStretch(1)

    # ------------------------------------------------------------------ #
    def load(self, config: NipoConfig) -> None:
        """Populate all controls from a config object."""
        gen = config.general
        self.token.setText(gen.token)
        self.protocol.setCurrentText(gen.protocol or "http")
        self.timeout.setValue(int(gen.timeout))
        self.pull_timeout.setValue(int(gen.pullTimeout))
        self.tunnel_enable.setChecked(gen.tunnelEnable)
        self.connection_reuse.setChecked(gen.connectionReuse)
        self.tls_enable.setChecked(gen.tlsEnable)
        self.tls_verify.setChecked(gen.tlsVerifyPeer)
        self.fake_urls.setPlainText(_list_to_text(gen.fakeUrls))
        self.methods.setText(", ".join(gen.methods))
        self.endpoints.setText(", ".join(gen.endPoints))
        self.tls_cert.setText(gen.tlsCertFile)
        self.tls_key.setText(gen.tlsKeyFile)
        self.tls_ca.setText(gen.tlsCaFile)

        ag = config.agent
        self.agent_threads.setValue(int(ag.threads))
        self.agent_listen_ip.setText(ag.listenIp)
        self.agent_listen_port.setValue(int(ag.listenPort))
        self.server_ip.setText(ag.serverIp)
        self.server_port.setValue(int(ag.serverPort))
        self.http_version.setText(ag.httpVersion)
        self.user_agent.setText(ag.userAgent)

        sv = config.server
        self.server_threads.setValue(int(sv.threads))
        self.server_listen_ip.setText(sv.listenIp)
        self.server_listen_port.setValue(int(sv.listenPort))

        lg = config.log
        self.log_level.setCurrentText(lg.logLevel or "INFO")
        self.log_file.setText(lg.logFile)

    def to_config(self) -> NipoConfig:
        """Read all controls back into a config object."""
        general = GeneralConfig(
            token=self.token.text().strip(),
            protocol=self.protocol.currentText(),
            fakeUrls=_text_to_list(self.fake_urls.toPlainText()),
            methods=_text_to_list(self.methods.text()),
            endPoints=_text_to_list(self.endpoints.text()),
            timeout=self.timeout.value(),
            pullTimeout=self.pull_timeout.value(),
            tunnelEnable=self.tunnel_enable.isChecked(),
            connectionReuse=self.connection_reuse.isChecked(),
            tlsEnable=self.tls_enable.isChecked(),
            tlsVerifyPeer=self.tls_verify.isChecked(),
            tlsCertFile=self.tls_cert.text().strip(),
            tlsKeyFile=self.tls_key.text().strip(),
            tlsCaFile=self.tls_ca.text().strip(),
        )
        agent = AgentConfig(
            threads=self.agent_threads.value(),
            listenIp=self.agent_listen_ip.text().strip(),
            listenPort=self.agent_listen_port.value(),
            serverIp=self.server_ip.text().strip(),
            serverPort=self.server_port.value(),
            httpVersion=self.http_version.text().strip(),
            userAgent=self.user_agent.text().strip(),
        )
        server = ServerConfig(
            threads=self.server_threads.value(),
            listenIp=self.server_listen_ip.text().strip(),
            listenPort=self.server_listen_port.value(),
        )
        log = LogConfig(
            logLevel=self.log_level.currentText(),
            logFile=self.log_file.text().strip(),
        )
        return NipoConfig(general=general, log=log, server=server, agent=agent)
