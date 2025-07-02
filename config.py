from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

@dataclass
class Config:
    """Comprehensive configuration for optimal performance."""

    # HTTP settings
    headers: Dict[str, str]
    request_timeout: int
    connect_timeout: float
    max_retries: int

    # Processing settings
    concurrent_limit: int
    max_configs_per_source: int

    # Protocol validation
    valid_prefixes: Tuple[str, ...]

    # Testing settings
    enable_url_testing: bool
    enable_sorting: bool
    test_timeout: float
    full_test: bool

    # Output settings
    output_dir: str

    # New features
    batch_size: int
    threshold: int
    top_n: int
    tls_fragment: Optional[str]
    include_protocols: Optional[Set[str]]
    exclude_protocols: Optional[Set[str]]
    resume_file: Optional[str]
    max_ping_ms: Optional[int]
    log_file: Optional[str]
    cumulative_batches: bool
    strict_batch: bool
    shuffle_sources: bool
    write_base64: bool
    write_csv: bool
    proxy: Optional[str]
    output_clash: bool
    prefer_protocols: Optional[List[str]]
    app_tests: Optional[List[str]]

CONFIG = Config(
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    },
    request_timeout=30,
    connect_timeout=3.0,
    max_retries=3,
    concurrent_limit=50,
    max_configs_per_source=75000,
    valid_prefixes=(
        "vmess://", "vless://", "ss://", "trojan://", "hy2://",
        "hysteria://", "hysteria2://", "tuic://", "reality://",
        "naive://", "juicity://", "shadowtls://", "wireguard://",
        "brook://", "socks://", "socks4://", "socks5://",
        "http://", "https://", "grpc://", "ws://", "wss://",
        "ssr://", "tcp://", "kcp://", "quic://", "h2://",
    ),
    enable_url_testing=True,
    enable_sorting=True,
    test_timeout=5.0,
    full_test=False,
    output_dir="output",
    batch_size=1000,
    threshold=0,
    top_n=0,
    tls_fragment=None,
    include_protocols=None,
    exclude_protocols=None,
    resume_file=None,
    max_ping_ms=1000,
    log_file=None,
    cumulative_batches=False,
    strict_batch=True,
    shuffle_sources=False,
    write_base64=True,
    write_csv=True,
    proxy=None,
    output_clash=False,
    prefer_protocols=None,
    app_tests=None,
)
