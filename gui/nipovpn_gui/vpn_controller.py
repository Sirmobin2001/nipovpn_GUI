"""Manage the NipoVPN core process (agent mode).

The controller writes the active configuration to a YAML file and launches the
imported core binary as ``<binary> agent <config.yaml>`` using :class:`QProcess`
so the GUI can stream its log output and react to start/stop events.
"""

from __future__ import annotations

import enum
import os
import tempfile

from PySide6.QtCore import QProcess, QObject, Signal

from .config_model import NipoConfig


class VpnState(enum.Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    ERROR = "Error"


class VpnController(QObject):
    """Owns the lifecycle of the core process."""

    state_changed = Signal(VpnState)
    log_line = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._core_path: str = ""
        self._config: NipoConfig | None = None
        self._state = VpnState.DISCONNECTED
        self._config_path = os.path.join(
            tempfile.gettempdir(), "nipovpn_gui_active.yaml"
        )
        self._process: QProcess | None = None

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #
    @property
    def core_path(self) -> str:
        return self._core_path

    def set_core_path(self, path: str) -> None:
        self._core_path = path

    @property
    def config(self) -> NipoConfig | None:
        return self._config

    def set_config(self, config: NipoConfig) -> None:
        self._config = config

    @property
    def state(self) -> VpnState:
        return self._state

    def is_running(self) -> bool:
        return (
            self._process is not None
            and self._process.state() != QProcess.NotRunning
        )

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def _set_state(self, state: VpnState) -> None:
        if state != self._state:
            self._state = state
            self.state_changed.emit(state)

    def can_start(self) -> tuple[bool, str]:
        if self.is_running():
            return False, "Already running."
        if not self._core_path:
            return False, "No core binary imported."
        if not os.path.isfile(self._core_path):
            return False, f"Core binary not found: {self._core_path}"
        if not os.access(self._core_path, os.X_OK):
            return False, "Core binary is not executable."
        if self._config is None:
            return False, "No configuration loaded."
        problems = self._config.validate()
        if problems:
            return False, "Invalid config: " + "; ".join(problems)
        return True, ""

    def start(self) -> tuple[bool, str]:
        ok, reason = self.can_start()
        if not ok:
            self.log_line.emit(f"[gui] Cannot start: {reason}")
            self._set_state(VpnState.ERROR)
            return False, reason

        assert self._config is not None
        try:
            self._config.to_yaml_file(self._config_path)
        except OSError as exc:
            self.log_line.emit(f"[gui] Failed to write config: {exc}")
            self._set_state(VpnState.ERROR)
            return False, str(exc)

        self._set_state(VpnState.CONNECTING)
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_output)
        self._process.started.connect(lambda: self._set_state(VpnState.CONNECTED))
        self._process.errorOccurred.connect(self._on_error)
        self._process.finished.connect(self._on_finished)

        self.log_line.emit(
            f"[gui] Starting: {self._core_path} agent {self._config_path}"
        )
        self._process.start(self._core_path, ["agent", self._config_path])
        return True, ""

    def stop(self) -> None:
        if self._process is not None and self.is_running():
            self.log_line.emit("[gui] Stopping core process...")
            self._process.terminate()
            if not self._process.waitForFinished(3000):
                self._process.kill()
                self._process.waitForFinished(2000)
        self._set_state(VpnState.DISCONNECTED)

    # ------------------------------------------------------------------ #
    # Process callbacks
    # ------------------------------------------------------------------ #
    def _on_output(self) -> None:
        if self._process is None:
            return
        data = self._process.readAllStandardOutput().data()
        text = bytes(data).decode("utf-8", errors="replace")
        for line in text.splitlines():
            if line.strip():
                self.log_line.emit(line)

    def _on_error(self, error: QProcess.ProcessError) -> None:
        self.log_line.emit(f"[gui] Process error: {error}")
        self._set_state(VpnState.ERROR)

    def _on_finished(self, code: int, status: QProcess.ExitStatus) -> None:
        self.log_line.emit(f"[gui] Core process exited (code={code}).")
        if self._state != VpnState.ERROR:
            self._set_state(VpnState.DISCONNECTED)
