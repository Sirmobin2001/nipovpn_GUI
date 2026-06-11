import base64

import pytest

from nipovpn_gui.config_model import (
    ConfigError,
    NipoConfig,
    decode_base64_config,
    encode_base64_config,
)

SAMPLE_YAML = """
general:
  token: "test-token"
  protocol: http
  fakeUrls:
    - example.com
  methods:
    - GET
  endPoints:
    - api
  timeout: 12
  pullTimeout: 40
  tunnelEnable: true
  connectionReuse: false
  tlsEnable: false
  tlsVerifyPeer: false
log:
  logLevel: DEBUG
  logFile: /tmp/nipo.log
server:
  threads: 4
  listenIp: 0.0.0.0
  listenPort: 80
agent:
  threads: 4
  listenIp: 127.0.0.1
  listenPort: 8080
  serverIp: 10.0.0.1
  serverPort: 443
  httpVersion: "1.1"
  userAgent: "test-agent"
"""


def test_from_yaml_parses_all_sections():
    cfg = NipoConfig.from_yaml(SAMPLE_YAML)
    assert cfg.general.token == "test-token"
    assert cfg.general.timeout == 12
    assert cfg.general.tunnelEnable is True
    assert cfg.general.connectionReuse is False
    assert cfg.agent.serverIp == "10.0.0.1"
    assert cfg.agent.serverPort == 443
    assert cfg.log.logLevel == "DEBUG"
    assert cfg.server.listenPort == 80


def test_partial_config_fills_defaults():
    cfg = NipoConfig.from_dict({"general": {"token": "abc"}})
    assert cfg.general.token == "abc"
    # Defaults preserved
    assert cfg.agent.listenPort == 8080
    assert "google.com" in cfg.general.fakeUrls


def test_unknown_keys_are_ignored():
    cfg = NipoConfig.from_dict({"general": {"token": "abc", "bogus": 1}})
    assert cfg.general.token == "abc"


def test_yaml_roundtrip():
    cfg = NipoConfig.from_yaml(SAMPLE_YAML)
    text = cfg.to_yaml()
    cfg2 = NipoConfig.from_yaml(text)
    assert cfg.to_dict() == cfg2.to_dict()


def test_base64_roundtrip():
    cfg = NipoConfig.from_yaml(SAMPLE_YAML)
    blob = cfg.to_base64()
    cfg2 = NipoConfig.from_base64(blob)
    assert cfg.to_dict() == cfg2.to_dict()


def test_decode_base64_standard():
    raw = "general:\n  token: hello\n"
    encoded = base64.b64encode(raw.encode()).decode()
    assert decode_base64_config(encoded) == raw


def test_decode_base64_urlsafe_without_padding():
    raw = "general:\n  token: padding-test-value\n"
    encoded = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
    assert decode_base64_config(encoded) == raw


def test_decode_base64_with_prefix_and_whitespace():
    raw = "general:\n  token: prefixed\n"
    encoded = "base64://" + base64.b64encode(raw.encode()).decode()
    spaced = encoded[:10] + "\n  " + encoded[10:]
    assert decode_base64_config(spaced) == raw


def test_decode_base64_invalid():
    with pytest.raises(ConfigError):
        decode_base64_config("!!!not base64!!!")


def test_decode_base64_empty():
    with pytest.raises(ConfigError):
        decode_base64_config("   ")


def test_encode_base64_helper():
    assert decode_base64_config(encode_base64_config("hi there")) == "hi there"


def test_from_yaml_empty_raises():
    with pytest.raises(ConfigError):
        NipoConfig.from_yaml("")


def test_from_yaml_invalid_raises():
    with pytest.raises(ConfigError):
        NipoConfig.from_yaml("general: [unclosed")


def test_validate_detects_problems():
    cfg = NipoConfig()
    cfg.general.token = ""
    cfg.agent.serverIp = ""
    cfg.agent.serverPort = 0
    problems = cfg.validate()
    assert any("token" in p for p in problems)
    assert any("serverIp" in p for p in problems)
    assert any("serverPort" in p for p in problems)


def test_validate_ok():
    cfg = NipoConfig.from_yaml(SAMPLE_YAML)
    assert cfg.validate() == []


def test_yaml_file_roundtrip(tmp_path):
    cfg = NipoConfig.from_yaml(SAMPLE_YAML)
    path = tmp_path / "config.yaml"
    cfg.to_yaml_file(str(path))
    cfg2 = NipoConfig.from_yaml_file(str(path))
    assert cfg.to_dict() == cfg2.to_dict()
