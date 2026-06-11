"""Configuration model for the NipoVPN GUI client.

This module mirrors the ``config.yaml`` schema understood by the NipoVPN C++
core (see ``core/src/config.cpp``). It provides a typed model plus helpers to:

* load / dump YAML (``import/export config.yaml``),
* decode / encode a base64 representation of a config (``base64 config import``),
* build a config from manual field input.

The model is intentionally free of any Qt dependency so it can be unit tested
in isolation.
"""

from __future__ import annotations

import base64
import binascii
import copy
from dataclasses import dataclass, field, asdict
from typing import Any

import yaml

# Default values that match ``nipovpn/etc/nipovpn/config.yaml``. They are used
# when a field is missing from imported data so the GUI always has a complete,
# valid configuration to work with.
DEFAULT_FAKE_URLS = [
    "nipo.ciron.net",
    "sudoer.ir",
    "sudoer.net",
    "google.com",
    "cloudflare.com",
]
DEFAULT_METHODS = ["GET", "POST", "PUT", "DELETE"]
DEFAULT_ENDPOINTS = ["api", "login", "user", "update"]
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) "
    "Gecko/20100101 Firefox/132.0"
)


class ConfigError(ValueError):
    """Raised when a config cannot be parsed or is structurally invalid."""


@dataclass
class GeneralConfig:
    token: str = ""
    protocol: str = "http"
    fakeUrls: list[str] = field(default_factory=lambda: list(DEFAULT_FAKE_URLS))
    methods: list[str] = field(default_factory=lambda: list(DEFAULT_METHODS))
    endPoints: list[str] = field(default_factory=lambda: list(DEFAULT_ENDPOINTS))
    timeout: int = 10
    pullTimeout: int = 50
    tunnelEnable: bool = False
    connectionReuse: bool = True
    tlsEnable: bool = False
    tlsVerifyPeer: bool = False
    tlsCertFile: str = "/etc/nipovpn/server.crt"
    tlsKeyFile: str = "/etc/nipovpn/server.key"
    tlsCaFile: str = ""


@dataclass
class LogConfig:
    logLevel: str = "INFO"
    logFile: str = "/var/log/nipovpn/nipovpn.log"


@dataclass
class ServerConfig:
    threads: int = 8
    listenIp: str = "0.0.0.0"
    listenPort: int = 80


@dataclass
class AgentConfig:
    threads: int = 8
    listenIp: str = "0.0.0.0"
    listenPort: int = 8080
    serverIp: str = "127.0.0.1"
    serverPort: int = 80
    httpVersion: str = "1.1"
    userAgent: str = DEFAULT_USER_AGENT


@dataclass
class NipoConfig:
    """Full NipoVPN configuration."""

    general: GeneralConfig = field(default_factory=GeneralConfig)
    log: LogConfig = field(default_factory=LogConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NipoConfig":
        """Build a config from a (possibly partial) dictionary.

        Missing sections / keys fall back to their defaults so the resulting
        config is always complete.
        """
        if not isinstance(data, dict):
            raise ConfigError("Configuration root must be a mapping/object.")

        def section(name: str, dc_type: type) -> Any:
            raw = data.get(name) or {}
            if not isinstance(raw, dict):
                raise ConfigError(f"Section '{name}' must be a mapping.")
            valid = {f.name for f in dc_type.__dataclass_fields__.values()}
            filtered = {k: v for k, v in raw.items() if k in valid}
            return dc_type(**filtered)

        return cls(
            general=section("general", GeneralConfig),
            log=section("log", LogConfig),
            server=section("server", ServerConfig),
            agent=section("agent", AgentConfig),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary matching the YAML schema."""
        return {
            "general": asdict(self.general),
            "log": asdict(self.log),
            "server": asdict(self.server),
            "agent": asdict(self.agent),
        }

    def copy(self) -> "NipoConfig":
        return copy.deepcopy(self)

    # ------------------------------------------------------------------ #
    # YAML (import / export config.yaml)
    # ------------------------------------------------------------------ #
    @classmethod
    def from_yaml(cls, text: str) -> "NipoConfig":
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML: {exc}") from exc
        if data is None:
            raise ConfigError("Configuration is empty.")
        return cls.from_dict(data)

    @classmethod
    def from_yaml_file(cls, path: str) -> "NipoConfig":
        with open(path, "r", encoding="utf-8") as handle:
            return cls.from_yaml(handle.read())

    def to_yaml(self) -> str:
        return yaml.safe_dump(
            self.to_dict(),
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )

    def to_yaml_file(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(self.to_yaml())

    # ------------------------------------------------------------------ #
    # Base64 (built-in base64 decoder for config import)
    # ------------------------------------------------------------------ #
    @classmethod
    def from_base64(cls, text: str) -> "NipoConfig":
        """Decode a base64 blob (containing YAML or JSON) into a config."""
        decoded = decode_base64_config(text)
        return cls.from_yaml(decoded)

    def to_base64(self) -> str:
        raw = self.to_yaml().encode("utf-8")
        return base64.b64encode(raw).decode("ascii")

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #
    def validate(self) -> list[str]:
        """Return a list of human readable problems (empty == valid)."""
        problems: list[str] = []
        if not self.general.token.strip():
            problems.append("General token is empty.")
        if self.general.protocol not in ("http", "socks5"):
            problems.append("Protocol must be 'http' or 'socks5'.")
        if not self.agent.serverIp.strip():
            problems.append("Agent serverIp is empty.")
        for label, port in (
            ("agent.listenPort", self.agent.listenPort),
            ("agent.serverPort", self.agent.serverPort),
            ("server.listenPort", self.server.listenPort),
        ):
            if not 0 < int(port) < 65536:
                problems.append(f"{label} must be between 1 and 65535.")
        return problems


def decode_base64_config(text: str) -> str:
    """Decode a base64 (standard or URL-safe) string to UTF-8 text.

    Whitespace and an optional ``base64://`` / ``data:`` style prefix are
    stripped, and missing padding is restored, so the decoder is forgiving of
    the many ways configs get shared.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        raise ConfigError("No base64 input provided.")

    for prefix in ("base64://", "nipovpn://"):
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix):]
    if cleaned.startswith("data:") and "," in cleaned:
        cleaned = cleaned.split(",", 1)[1]

    cleaned = "".join(cleaned.split())
    # Normalize URL-safe alphabet to the standard one.
    cleaned = cleaned.replace("-", "+").replace("_", "/")
    # Restore padding.
    missing = len(cleaned) % 4
    if missing:
        cleaned += "=" * (4 - missing)

    try:
        raw = base64.b64decode(cleaned, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ConfigError(f"Invalid base64 data: {exc}") from exc

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigError("Decoded data is not valid UTF-8 text.") from exc


def encode_base64_config(text: str) -> str:
    """Encode arbitrary config text as standard base64."""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")
