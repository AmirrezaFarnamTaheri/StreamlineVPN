import pytest
from streamline_vpn.merger.advanced_converters import generate_surge_conf, generate_qx_conf

# Fixtures for proxy data
@pytest.fixture
def vmess_proxy():
    return {
        "name": "vmess-ws-tls",
        "type": "vmess",
        "server": "example.com",
        "port": 443,
        "uuid": "a-uuid-string",
        "alterId": 0,
        "cipher": "auto",
        "tls": True,
        "sni": "example.com",
        "network": "ws",
        "ws-opts": {"path": "/path", "headers": {"Host": "example.com"}},
        "path": "/path",
        "host": "example.com",
    }

@pytest.fixture
def ss_proxy():
    return {
        "name": "ss-proxy",
        "type": "ss",
        "server": "ss.example.com",
        "port": 8443,
        "cipher": "aes-256-gcm",
        "password": "a-password",
    }

@pytest.fixture
def trojan_grpc_proxy():
    return {
        "name": "trojan-grpc",
        "type": "trojan",
        "server": "grpc.example.com",
        "port": 443,
        "password": "a-password",
        "sni": "grpc.example.com",
        "network": "grpc",
        "grpc-opts": {"grpc-service-name": "com.service.Name"},
        "serviceName": "com.service.Name",
    }

# Tests for generate_surge_conf
def test_generate_surge_conf_empty():
    assert generate_surge_conf([]) == "[Proxy]"

def test_generate_surge_conf_single_vmess(vmess_proxy):
    expected = (
        "[Proxy]\n"
        "vmess-ws-tls = vmess, example.com, 443, username=a-uuid-string, tls=true, sni=example.com, ws=true, ws-path=/path, ws-headers=Host:example.com"
    )
    assert generate_surge_conf([vmess_proxy]) == expected

def test_generate_surge_conf_single_ss(ss_proxy):
    expected = (
        "[Proxy]\n"
        "ss-proxy = ss, ss.example.com, 8443, encrypt-method=aes-256-gcm, password=a-password"
    )
    assert generate_surge_conf([ss_proxy]) == expected

def test_generate_surge_conf_multiple(vmess_proxy, ss_proxy, trojan_grpc_proxy):
    expected = (
        "[Proxy]\n"
        "vmess-ws-tls = vmess, example.com, 443, username=a-uuid-string, tls=true, sni=example.com, ws=true, ws-path=/path, ws-headers=Host:example.com\n"
        "ss-proxy = ss, ss.example.com, 8443, encrypt-method=aes-256-gcm, password=a-password\n"
        "trojan-grpc = trojan, grpc.example.com, 443, password=a-password, sni=grpc.example.com, grpc=true, grpc-service-name=com.service.Name"
    )
    assert generate_surge_conf([vmess_proxy, ss_proxy, trojan_grpc_proxy]) == expected

# Tests for generate_qx_conf
def test_generate_qx_conf_empty():
    assert generate_qx_conf([]) == ""

def test_generate_qx_conf_single_vmess(vmess_proxy):
    expected = "vmess=example.com:443, id=a-uuid-string, method=auto, tls=true, tls-host=example.com, obfs=ws, obfs-host=example.com, obfs-uri=/path, tag=vmess-ws-tls"
    assert generate_qx_conf([vmess_proxy]) == expected

def test_generate_qx_conf_single_ss(ss_proxy):
    expected = "ss=ss.example.com:8443, password=a-password, method=aes-256-gcm, tag=ss-proxy"
    assert generate_qx_conf([ss_proxy]) == expected

def test_generate_qx_conf_multiple(vmess_proxy, ss_proxy, trojan_grpc_proxy):
    expected = (
        "vmess=example.com:443, id=a-uuid-string, method=auto, tls=true, tls-host=example.com, obfs=ws, obfs-host=example.com, obfs-uri=/path, tag=vmess-ws-tls\n"
        "ss=ss.example.com:8443, password=a-password, method=aes-256-gcm, tag=ss-proxy\n"
        "trojan=grpc.example.com:443, password=a-password, tls-host=grpc.example.com, obfs=grpc, grpc-service-name=com.service.Name, tag=trojan-grpc"
    )
    assert generate_qx_conf([vmess_proxy, ss_proxy, trojan_grpc_proxy]) == expected


def test_generate_surge_conf_missing_optional_params():
    proxies = [
        # ws without path/host
        {
            "name": "vmess-ws-no-opts", "type": "vmess", "server": "e.com", "port": 443,
            "uuid": "uuid1", "network": "ws"
        },
        # grpc without serviceName
        {
            "name": "trojan-grpc-no-opts", "type": "trojan", "server": "e.com", "port": 443,
            "password": "pwd", "network": "grpc"
        },
        # non-ss without password
        {
            "name": "trojan-no-pwd", "type": "trojan", "server": "e.com", "port": 443
        }
    ]
    expected = (
        "[Proxy]\n"
        "vmess-ws-no-opts = vmess, e.com, 443, username=uuid1, ws=true\n"
        "trojan-grpc-no-opts = trojan, e.com, 443, password=pwd, grpc=true\n"
        "trojan-no-pwd = trojan, e.com, 443"
    )
    assert generate_surge_conf(proxies) == expected


def test_generate_qx_conf_missing_optional_params():
    proxies = [
        # ws without path/host
        {
            "name": "vmess-ws-no-opts", "type": "vmess", "server": "e.com", "port": 443,
            "uuid": "uuid1", "network": "ws"
        },
        # grpc without serviceName
        {
            "name": "trojan-grpc-no-opts", "type": "trojan", "server": "e.com", "port": 443,
            "password": "pwd", "network": "grpc"
        }
    ]
    expected = (
        "vmess=e.com:443, id=uuid1, obfs=ws, tag=vmess-ws-no-opts\n"
        "trojan=e.com:443, password=pwd, obfs=grpc, tag=trojan-grpc-no-opts"
    )
    assert generate_qx_conf(proxies) == expected


def test_generate_surge_conf_non_ss_with_password():
    proxies = [{
        "name": "trojan-with-pwd",
        "type": "trojan",
        "server": "e.com",
        "port": 443,
        "password": "pwd"
    }]
    expected = "[Proxy]\n" \
               "trojan-with-pwd = trojan, e.com, 443, password=pwd"
    assert generate_surge_conf(proxies) == expected
