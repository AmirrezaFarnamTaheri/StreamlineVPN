"""
Protocol Handler
===============

Unified protocol parser for VPN configurations.
This module consolidates all protocol parsing functionality to eliminate duplication.
"""

import logging
import re
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlparse

from ..models.configuration import VPNConfiguration

logger = logging.getLogger(__name__)


class ProtocolParser:
    """Unified protocol parser for VPN configurations.
    
    This class consolidates all protocol parsing functionality that was previously
    duplicated across multiple modules. It provides both dictionary output for
    internal processing and VPNConfiguration objects for the main application.
    """
    
    def __init__(self):
        """Initialize the protocol parser."""
        self.protocol_handlers = {
            'vmess': self._parse_vmess,
            'vless': self._parse_vless,
            'trojan': self._parse_trojan,
            'shadowsocks': self._parse_shadowsocks,
            'http': self._parse_http,
            'socks': self._parse_socks
        }
        self.parsed_configs: List[VPNConfiguration] = []
        self.duplicate_count = 0
    
    def parse_to_dict(self, config_line: str) -> Optional[Dict[str, Any]]:
        """Parse configuration to dictionary format.
        
        Args:
            config_line: Configuration line to parse
            
        Returns:
            Parsed configuration dictionary or None
        """
        if not config_line or not config_line.strip():
            return None
        
        config_line = config_line.strip()
        protocol = self._detect_protocol(config_line)
        
        if not protocol:
            return None
        
        handler = self.protocol_handlers.get(protocol)
        if not handler:
            return None
        
        try:
            return handler(config_line, return_dict=True)
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to parse {protocol} config: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing {protocol} config: {e}")
            return None
    
    def parse_to_config(self, config_line: str, source_url: str = "") -> Optional[VPNConfiguration]:
        """Parse configuration to VPNConfiguration object.
        
        Args:
            config_line: Configuration line to parse
            source_url: Source URL for tracking
            
        Returns:
            VPNConfiguration object or None if invalid
        """
        if not config_line or not config_line.strip():
            return None
        
        config_line = config_line.strip()
        protocol = self._detect_protocol(config_line)
        
        if not protocol:
            logger.debug(f"Unknown protocol for config: {config_line[:50]}...")
            return None
        
        handler = self.protocol_handlers.get(protocol)
        if not handler:
            logger.warning(f"No handler for protocol: {protocol}")
            return None
        
        try:
            config = handler(config_line, source_url, return_dict=False)
            if config and not self._is_duplicate(config):
                self.parsed_configs.append(config)
                return config
            elif config:
                self.duplicate_count += 1
                logger.debug(f"Duplicate config detected: {config.server}:{config.port}")
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            logger.debug(f"Error processing config: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing config: {e}")
        
        return None
    
    def _detect_protocol(self, config_line: str) -> Optional[str]:
        """Detect the protocol from configuration line.
        
        Args:
            config_line: Configuration line to analyze
            
        Returns:
            Detected protocol or None
        """
        config_lower = config_line.lower()
        
        if config_line.startswith('vmess://'):
            return 'vmess'
        elif config_line.startswith('vless://'):
            return 'vless'
        elif config_line.startswith('trojan://'):
            return 'trojan'
        elif config_line.startswith('ss://'):
            return 'shadowsocks'
        elif config_line.startswith('http://') or config_line.startswith('https://'):
            return 'http'
        elif config_line.startswith('socks://'):
            return 'socks'
        
        # Check for protocol indicators in the content
        if 'vmess' in config_lower:
            return 'vmess'
        elif 'vless' in config_lower:
            return 'vless'
        elif 'trojan' in config_lower:
            return 'trojan'
        elif 'shadowsocks' in config_lower or 'ss://' in config_lower:
            return 'shadowsocks'
        
        return None
    
    def _parse_vmess(self, config_line: str, source_url: str = "", return_dict: bool = False) -> Optional[Union[Dict[str, Any], VPNConfiguration]]:
        """Parse VMess configuration.
        
        Args:
            config_line: VMess configuration line
            source_url: Source URL
            return_dict: If True, return dictionary; if False, return VPNConfiguration
            
        Returns:
            Parsed configuration or None
        """
        try:
            import base64
            import json
            
            encoded_part = config_line[8:]  # Remove 'vmess://'
            decoded = base64.b64decode(encoded_part).decode('utf-8')
            config_data = json.loads(decoded)
            
            if return_dict:
                return {
                    'protocol': 'vmess',
                    'server': config_data.get('add', ''),
                    'port': config_data.get('port', 0),
                    'uuid': config_data.get('id', ''),
                    'alter_id': config_data.get('aid', 0),
                    'network': config_data.get('net', 'tcp'),
                    'security': config_data.get('tls', ''),
                    'host': config_data.get('host', ''),
                    'path': config_data.get('path', '')
                }
            else:
                return VPNConfiguration(
                    protocol='vmess',
                    server=config_data.get('add', ''),
                    port=config_data.get('port', 0),
                    uuid=config_data.get('id', ''),
                    alter_id=config_data.get('aid', 0),
                    network=config_data.get('net', 'tcp'),
                    security=config_data.get('tls', ''),
                    host=config_data.get('host', ''),
                    path=config_data.get('path', ''),
                    source_url=source_url,
                    quality_score=0.8
                )
        except Exception as e:
            logger.debug(f"Failed to parse VMess config: {e}")
            return None
    
    def _parse_vless(self, config_line: str, source_url: str = "", return_dict: bool = False) -> Optional[Union[Dict[str, Any], VPNConfiguration]]:
        """Parse VLESS configuration."""
        try:
            url_part = config_line[8:]  # Remove 'vless://'
            parsed = urlparse(f"http://{url_part}")
            
            auth_part = parsed.netloc.split('@')
            if len(auth_part) != 2:
                return None
            
            uuid = auth_part[0]
            server_port = auth_part[1].split(':')
            if len(server_port) != 2:
                return None
            
            server = server_port[0]
            port = int(server_port[1])
            
            if return_dict:
                return {
                    'protocol': 'vless',
                    'server': server,
                    'port': port,
                    'uuid': uuid
                }
            else:
                return VPNConfiguration(
                    protocol='vless',
                    server=server,
                    port=port,
                    uuid=uuid,
                    source_url=source_url,
                    quality_score=0.9
                )
        except Exception as e:
            logger.debug(f"Failed to parse VLESS config: {e}")
            return None
    
    def _parse_trojan(self, config_line: str, source_url: str = "", return_dict: bool = False) -> Optional[Union[Dict[str, Any], VPNConfiguration]]:
        """Parse Trojan configuration."""
        try:
            url_part = config_line[9:]  # Remove 'trojan://'
            parsed = urlparse(f"http://{url_part}")
            
            auth_part = parsed.netloc.split('@')
            if len(auth_part) != 2:
                return None
            
            password = auth_part[0]
            server_port = auth_part[1].split(':')
            if len(server_port) != 2:
                return None
            
            server = server_port[0]
            port = int(server_port[1])
            
            if return_dict:
                return {
                    'protocol': 'trojan',
                    'server': server,
                    'port': port,
                    'password': password
                }
            else:
                return VPNConfiguration(
                    protocol='trojan',
                    server=server,
                    port=port,
                    password=password,
                    source_url=source_url,
                    quality_score=0.85
                )
        except Exception as e:
            logger.debug(f"Failed to parse Trojan config: {e}")
            return None
    
    def _parse_shadowsocks(self, config_line: str, source_url: str = "", return_dict: bool = False) -> Optional[Union[Dict[str, Any], VPNConfiguration]]:
        """Parse Shadowsocks configuration."""
        try:
            import base64
            
            encoded_part = config_line[5:]  # Remove 'ss://'
            decoded = base64.b64decode(encoded_part).decode('utf-8')
            
            parts = decoded.split('@')
            if len(parts) != 2:
                return None
            
            method_password = parts[0].split(':')
            if len(method_password) != 2:
                return None
            
            method = method_password[0]
            password = method_password[1]
            
            server_port = parts[1].split(':')
            if len(server_port) != 2:
                return None
            
            server = server_port[0]
            port = int(server_port[1])
            
            if return_dict:
                return {
                    'protocol': 'shadowsocks',
                    'server': server,
                    'port': port,
                    'method': method,
                    'password': password
                }
            else:
                return VPNConfiguration(
                    protocol='shadowsocks',
                    server=server,
                    port=port,
                    method=method,
                    password=password,
                    source_url=source_url,
                    quality_score=0.7
                )
        except Exception as e:
            logger.debug(f"Failed to parse Shadowsocks config: {e}")
            return None
    
    def _parse_http(self, config_line: str, source_url: str = "", return_dict: bool = False) -> Optional[Union[Dict[str, Any], VPNConfiguration]]:
        """Parse HTTP proxy configuration."""
        try:
            parsed = urlparse(config_line)
            server = parsed.hostname
            port = parsed.port or 80
            
            if return_dict:
                return {
                    'protocol': 'http',
                    'server': server,
                    'port': port
                }
            else:
                return VPNConfiguration(
                    protocol='http',
                    server=server,
                    port=port,
                    source_url=source_url,
                    quality_score=0.5
                )
        except Exception as e:
            logger.debug(f"Failed to parse HTTP config: {e}")
            return None
    
    def _parse_socks(self, config_line: str, source_url: str = "", return_dict: bool = False) -> Optional[Union[Dict[str, Any], VPNConfiguration]]:
        """Parse SOCKS proxy configuration."""
        try:
            parsed = urlparse(config_line)
            server = parsed.hostname
            port = parsed.port or 1080
            
            if return_dict:
                return {
                    'protocol': 'socks',
                    'server': server,
                    'port': port
                }
            else:
                return VPNConfiguration(
                    protocol='socks',
                    server=server,
                    port=port,
                    source_url=source_url,
                    quality_score=0.6
                )
        except Exception as e:
            logger.debug(f"Failed to parse SOCKS config: {e}")
            return None
    
    def _is_duplicate(self, config: VPNConfiguration) -> bool:
        """Check if configuration is a duplicate."""
        for existing in self.parsed_configs:
            if (existing.server == config.server and 
                existing.port == config.port and 
                existing.protocol == config.protocol):
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        protocol_counts = {}
        for config in self.parsed_configs:
            protocol = config.protocol
            protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
        
        return {
            'total_parsed': len(self.parsed_configs),
            'duplicates_found': self.duplicate_count,
            'protocol_distribution': protocol_counts
        }


# Backward compatibility alias
EnhancedConfigProcessor = ProtocolParser
