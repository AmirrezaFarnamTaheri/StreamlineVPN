from vpn_merger.security.security_manager import SecurityManager, SecurityError


def test_sanitize_host_ip():
    assert SecurityManager.sanitize_host('1.2.3.4') == '1.2.3.4'


def test_sanitize_host_domain_ok():
    assert SecurityManager.sanitize_host('example.com') == 'example.com'


def test_sanitize_host_invalid():
    try:
        SecurityManager.sanitize_host('bad host\n')
    except SecurityError:
        pass
    else:
        assert False, 'expected SecurityError'


def test_sanitize_port():
    assert SecurityManager.sanitize_port(443) == 443
    assert SecurityManager.sanitize_port(0) is None
    assert SecurityManager.sanitize_port(70000) is None

