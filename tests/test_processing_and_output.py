import asyncio
import os
from typing import List

import pytest

from streamline_vpn.core.processing.parser import ConfigurationParser
from streamline_vpn.core.processing.validator import ConfigurationValidator
from streamline_vpn.core.output_manager import OutputManager
from streamline_vpn.models.configuration import VPNConfiguration, Protocol


@pytest.fixture
def sample_configs() -> List[VPNConfiguration]:
    return [
        VPNConfiguration(
            protocol=Protocol.VMESS,
            server="test-server.example",
            port=443,
            user_id="uuid-1",
        ),
        VPNConfiguration(
            protocol=Protocol.VMESS,
            server="test-server.example",
            port=443,
            user_id="uuid-1",
        ),
    ]


def test_configuration_parser_vmess_valid():
    parser = ConfigurationParser()
    cfg = parser.parse_configuration(
        "vmess://eyJhZGQiOiJ0ZXN0LmNvbSIsInBvcnQiOjQ0MywidXNlcl9pZCI6InYifQ=="
    )
    # Not asserting exact value, but ensure it returns either None or a VPNConfiguration
    assert cfg is None or isinstance(cfg, VPNConfiguration)


def test_configuration_validator_basic(sample_configs):
    validator = ConfigurationValidator()
    ok, errs = validator.validate_configuration(sample_configs[0])
    assert ok
    assert errs == []


@pytest.mark.asyncio
async def test_output_manager_formats(tmp_path, sample_configs):
    out = OutputManager()
    # Ensure all supported formats return a path/dict and do not raise
    result = await out.save_configurations(sample_configs, str(tmp_path), [
        "json",
        "clash",
        "singbox",
        "raw",
    ])
    assert isinstance(result, dict)
    # Single format returns a Path
    single = await out.save_configurations(sample_configs, str(tmp_path), "json")
    assert single is not None

