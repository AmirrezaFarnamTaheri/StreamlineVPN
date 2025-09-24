from streamline_vpn.core.processing.parser import ConfigurationParser

def test_invalid_vmess_config_is_disabled():
    parser = ConfigurationParser()
    # Invalid vmess config missing 'add' field
    vmess_cfg = "vmess://ewogICJwb3J0IjogNDQzLAogICJpZCI6ICJ1dWlkLTEiLAogICJuZXQiOiAid3MiLAogICJwYXRoIjogIi93cyIsCiAgImhvc3QiOiAiaG9zdC50ZXN0LXNlcnZlci5leGFtcGxlIiwKICAidGxzIjogInRscyIsCiAgInNjeSI6ICJhdXRvIgp9Cg=="
    config = parser.parse_configuration(vmess_cfg)
    assert config is None

def test_invalid_vless_config_is_disabled():
    parser = ConfigurationParser()
    # Invalid vless config missing 'host'
    vless_cfg = "vless://user@:8443?type=ws&path=%2Fws&host=ex.com&security=tls"
    config = parser.parse_configuration(vless_cfg)
    assert config is None
