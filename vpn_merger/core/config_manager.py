from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Union
import yaml
import os
import json
from pathlib import Path
from pydantic import BaseModel, validator, Field
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class OutputFormat(str, Enum):
    RAW = "raw"
    BASE64 = "base64"
    CLASH = "clash"
    SINGBOX = "singbox"
    QUANTUMULT = "quantumult"
    V2RAY = "v2ray"


class NetworkConfig(BaseModel):
    concurrent_limit: int = Field(default=50, ge=1, le=200, description="Number of concurrent requests")
    request_timeout: int = Field(default=30, ge=5, le=120, description="HTTP request timeout in seconds")
    connect_timeout: float = Field(default=3.0, ge=0.1, le=30.0, description="TCP connection timeout")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")
    proxy: Optional[str] = Field(default=None, description="HTTP/SOCKS proxy URL")

    @validator('proxy')
    def validate_proxy(cls, v):
        if v is not None:
            if not (v.startswith('http://') or v.startswith('socks5://') or v.startswith('socks4://')):
                raise ValueError('Proxy must start with http://, socks4://, or socks5://')
        return v


class TestingConfig(BaseModel):
    enable_url_testing: bool = Field(default=True, description="Enable server reachability testing")
    enable_sorting: bool = Field(default=True, description="Enable performance-based sorting")
    test_timeout: float = Field(default=5.0, ge=0.1, le=60.0, description="Connection test timeout")
    full_test: bool = Field(default=False, description="Perform full TLS handshake")
    max_ping_ms: Optional[int] = Field(default=1000, ge=10, le=10000, description="Maximum acceptable ping")
    enable_distributed_testing: bool = Field(default=False, description="Enable multi-node testing")
    app_tests: Optional[List[str]] = Field(default=None, description="Services to test connectivity")

    @validator('app_tests')
    def validate_app_tests(cls, v):
        if v is not None:
            valid_apps = {'telegram', 'youtube', 'google', 'cloudflare'}
            for app in v:
                if app.lower() not in valid_apps:
                    raise ValueError(f'Invalid app test: {app}. Valid options: {valid_apps}')
        return v


class ProcessingConfig(BaseModel):
    max_configs_per_source: int = Field(default=75000, ge=100, le=500000, description="Max configs per source")
    batch_size: int = Field(default=1000, ge=0, le=10000, description="Batch processing size")
    threshold: int = Field(default=0, ge=0, description="Stop after N configs (0=unlimited)")
    top_n: int = Field(default=0, ge=0, description="Keep only top N configs (0=all)")
    cumulative_batches: bool = Field(default=False, description="Make batches cumulative")
    strict_batch: bool = Field(default=True, description="Strict batch size enforcement")
    shuffle_sources: bool = Field(default=False, description="Randomize source processing order")


class FilteringConfig(BaseModel):
    include_protocols: Optional[Set[str]] = Field(default=None, description="Protocols to include")
    exclude_protocols: Optional[Set[str]] = Field(default=None, description="Protocols to exclude")
    tls_fragment: Optional[str] = Field(default=None, description="Filter by TLS fragment content")
    prefer_protocols: Optional[List[str]] = Field(default=None, description="Protocol priority order")

    valid_prefixes: Set[str] = Field(default={
        "proxy://", "ss://", "clash://", "v2ray://", "reality://", "vmess://",
        "xray://", "wireguard://", "ech://", "vless://", "hysteria://", "tuic://",
        "sing-box://", "singbox://", "shadowtls://", "clashmeta://", "hysteria2://"
    }, description="Valid config prefixes")


class OutputConfig(BaseModel):
    output_dir: Path = Field(default=Path("output"), description="Output directory path")
    write_base64: bool = Field(default=True, description="Generate base64 output")
    write_csv: bool = Field(default=True, description="Generate CSV report")
    output_formats: List[OutputFormat] = Field(
        default=[OutputFormat.RAW, OutputFormat.BASE64, OutputFormat.CLASH],
        description="Output formats to generate"
    )
    output_clash: bool = Field(default=False, description="Generate Clash YAML")

    @validator('output_dir')
    def validate_output_dir(cls, v):
        resolved = v.resolve()
        try:
            resolved.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Cannot create output directory {resolved}: {e}")
        return resolved


class AdvancedConfig(BaseModel):
    tls_fragment_size: Optional[int] = Field(default=150, ge=50, le=1000, description="TLS fragment size")
    tls_fragment_sleep: Optional[int] = Field(default=15, ge=1, le=1000, description="TLS fragment sleep (ms)")
    mux_enable: bool = Field(default=False, description="Enable connection multiplexing")
    mux_protocol: str = Field(default="smux", regex="^(smux|yamux|h2mux)$", description="MUX protocol")
    mux_max_connections: int = Field(default=4, ge=1, le=20, description="Max MUX connections")
    mux_min_streams: int = Field(default=4, ge=1, le=100, description="Min streams per connection")
    mux_max_streams: int = Field(default=16, ge=1, le=100, description="Max streams per connection")
    mux_padding: bool = Field(default=False, description="Enable MUX padding")
    mux_brutal: bool = Field(default=False, description="Enable brutal congestion control")


class MonitoringConfig(BaseModel):
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    enable_dashboard: bool = Field(default=True, description="Enable web dashboard")
    metrics_port: int = Field(default=8001, ge=1024, le=65535, description="Metrics server port")
    dashboard_port: int = Field(default=8000, ge=1024, le=65535, description="Dashboard port")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    log_file: Optional[Path] = Field(default=None, description="Log file path")


class VPNMergerConfig(BaseModel):
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    testing: TestingConfig = Field(default_factory=TestingConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    filtering: FilteringConfig = Field(default_factory=FilteringConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    advanced: AdvancedConfig = Field(default_factory=AdvancedConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    resume_file: Optional[Path] = Field(default=None, description="Resume from existing file")

    class Config:
        env_prefix = 'VPN_MERGER_'
        env_nested_delimiter = '__'
        case_sensitive = False

    @validator('advanced')
    def validate_mux_streams(cls, v):
        if v.mux_min_streams > v.mux_max_streams:
            raise ValueError("mux_min_streams cannot be greater than mux_max_streams")
        return v


class ConfigManager:
    def __init__(self):
        self.config: Optional[VPNMergerConfig] = None
        self.config_paths = [
            Path.home() / ".vpn-merger" / "config.yaml",
            Path.cwd() / "config.yaml",
            Path.cwd() / "config" / "vpn-merger.yaml"
        ]

    def load_config(self, config_path: Optional[Path] = None, **override_kwargs) -> VPNMergerConfig:
        config_dict: Dict[str, Any] = {}

        if config_path:
            config_dict.update(self._load_from_file(config_path))
        else:
            for path in self.config_paths:
                if path.exists():
                    config_dict.update(self._load_from_file(path))
                    break

        config_dict.update(self._load_from_env())

        if override_kwargs:
            config_dict.update(self._flatten_overrides(override_kwargs))

        try:
            self.config = VPNMergerConfig(**config_dict)
            return self.config
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")

    def _load_from_file(self, config_path: Path) -> Dict[str, Any]:
        try:
            content = config_path.read_text(encoding='utf-8')
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(content) or {}
            elif config_path.suffix.lower() == '.json':
                return json.loads(content)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
            return {}

    def _load_from_env(self) -> Dict[str, Any]:
        env_config: Dict[str, Any] = {}
        prefix = 'VPN_MERGER_'
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                if '__' in config_key:
                    parts = config_key.split('__')
                    current: Dict[str, Any] = env_config
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = self._convert_env_value(value)
                else:
                    env_config[config_key] = self._convert_env_value(value)
        return env_config

    def _convert_env_value(self, value: str) -> Union[str, int, float, bool, List[str], None]:
        if value.lower() in ['none', 'null', '']:
            return None
        if value.lower() in ['true', 'yes', '1']:
            return True
        if value.lower() in ['false', 'no', '0']:
            return False
        if ',' in value:
            return [item.strip() for item in value.split(',') if item.strip()]
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        return value

    def _flatten_overrides(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        flattened: Dict[str, Any] = {}
        for key, value in overrides.items():
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    flattened[f"{key}__{nested_key}"] = nested_value
            else:
                flattened[key] = value
        return flattened

    def save_config(self, config_path: Path, config: Optional[VPNMergerConfig] = None):
        if config is None:
            config = self.config
        if config is None:
            raise ValueError("No configuration to save")
        config_dict = config.dict(exclude_none=True)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
        elif config_path.suffix.lower() == '.json':
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")


