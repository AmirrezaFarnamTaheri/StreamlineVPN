from streamline_vpn.core.processing.parser import ConfigurationParser
from streamline_vpn.models.configuration import Protocol


def test_parse_http():
    parser = ConfigurationParser()
    http_cfg = "http://user:pass@http.test-server.example:8080"
    cfg = parser.parse_configuration(http_cfg)
    assert cfg is not None
    assert cfg.protocol == Protocol.HTTP
    assert cfg.server == "http.test-server.example"
    assert cfg.port == 8080
    assert cfg.user_id == "user"
    assert cfg.password == "pass"

    http_cfg_no_auth = "http://http.test-server.example:8080"
    cfg = parser.parse_configuration(http_cfg_no_auth)
    assert cfg is not None
    assert cfg.protocol == Protocol.HTTP
    assert cfg.server == "http.test-server.example"
    assert cfg.port == 8080
    assert cfg.user_id == ""
    assert cfg.password == ""


def test_parse_socks5():
    parser = ConfigurationParser()
    socks5_cfg = "socks5://user:pass@socks5.test-server.example:1080"
    cfg = parser.parse_configuration(socks5_cfg)
    assert cfg is not None
    assert cfg.protocol == Protocol.SOCKS5
    assert cfg.server == "socks5.test-server.example"
    assert cfg.port == 1080
    assert cfg.user_id == "user"
    assert cfg.password == "pass"

    socks5_cfg_no_auth = "socks5://socks5.test-server.example:1080"
    cfg = parser.parse_configuration(socks5_cfg_no_auth)
    assert cfg is not None
    assert cfg.protocol == Protocol.SOCKS5
    assert cfg.server == "socks5.test-server.example"
    assert cfg.port == 1080
    assert cfg.user_id == ""
    assert cfg.password == ""


def test_parse_tuic():
    parser = ConfigurationParser()
    tuic_cfg = "tuic://uuid:password@tuic.test-server.example:8443?congestion_control=bbr&udp_relay_mode=native"
    cfg = parser.parse_configuration(tuic_cfg)
    assert cfg is not None
    assert cfg.protocol == Protocol.TUIC
    assert cfg.server == "tuic.test-server.example"
    assert cfg.port == 8443
    assert cfg.uuid == "uuid"
    assert cfg.password == "password"
    assert cfg.metadata["congestion_control"] == "bbr"
    assert cfg.metadata["udp_relay_mode"] == "native"
