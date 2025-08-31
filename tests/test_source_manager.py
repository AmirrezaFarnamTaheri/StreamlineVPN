"""
Test Source Manager
==================

Focused tests for source management functionality.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
import yaml

from vpn_merger.core.source_manager import SourceManager


class TestSourceManager:
    """Test the SourceManager class comprehensively."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        config_data = {
            'sources': {
                'tier_1_premium': {
                    'urls': [
                        {'url': 'https://example1.com/config1.txt'},
                        {'url': 'https://example2.com/config2.txt'}
                    ]
                },
                'tier_2_reliable': [
                    'https://example3.com/config3.txt',
                    'https://example4.com/config4.txt'
                ],
                'tier_3_bulk': {
                    'nested': {
                        'urls': [
                            {'url': 'https://example5.com/config5.txt'},
                            {'url': 'https://example6.com/config6.txt'}
                        ]
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        os.unlink(temp_file)
    
    @pytest.fixture
    def source_manager(self, temp_config_file):
        """Create a SourceManager instance with test config."""
        return SourceManager(temp_config_file)
    
    def test_initialization(self, source_manager):
        """Test SourceManager initialization."""
        assert source_manager is not None
        assert source_manager.config_path is not None
        assert isinstance(source_manager.sources, dict)
        assert len(source_manager.sources) > 0
    
    def test_load_sources_from_file(self, source_manager):
        """Test loading sources from YAML file."""
        sources = source_manager.sources
        
        # Check tier_1_premium (structured format)
        assert 'tier_1_premium' in sources
        tier1_urls = sources['tier_1_premium']
        assert len(tier1_urls) == 2
        assert 'https://example1.com/config1.txt' in tier1_urls
        assert 'https://example2.com/config2.txt' in tier1_urls
        
        # Check tier_2_reliable (simple list format)
        assert 'tier_2_reliable' in sources
        tier2_urls = sources['tier_2_reliable']
        assert len(tier2_urls) == 2
        assert 'https://example3.com/config3.txt' in tier2_urls
        assert 'https://example4.com/config4.txt' in tier2_urls
        
        # Check tier_3_bulk (nested structure)
        assert 'tier_3_bulk' in sources
        tier3_urls = sources['tier_3_bulk']
        assert len(tier3_urls) == 2
        assert 'https://example5.com/config5.txt' in tier3_urls
        assert 'https://example6.com/config6.txt' in tier3_urls
    
    def test_get_all_sources(self, source_manager):
        """Test getting all sources as a flat list."""
        all_sources = source_manager.get_all_sources()
        
        # Should have 6 total sources
        assert len(all_sources) == 6
        
        # Check that all expected URLs are present
        expected_urls = [
            'https://example1.com/config1.txt',
            'https://example2.com/config2.txt',
            'https://example3.com/config3.txt',
            'https://example4.com/config4.txt',
            'https://example5.com/config5.txt',
            'https://example6.com/config6.txt'
        ]
        
        for url in expected_urls:
            assert url in all_sources
    
    def test_get_sources_by_tier(self, source_manager):
        """Test getting sources from a specific tier."""
        tier1_sources = source_manager.get_sources_by_tier('tier_1_premium')
        assert len(tier1_sources) == 2
        assert 'https://example1.com/config1.txt' in tier1_sources
        
        tier2_sources = source_manager.get_sources_by_tier('tier_2_reliable')
        assert len(tier2_sources) == 2
        assert 'https://example3.com/config3.txt' in tier2_sources
        
        # Test non-existent tier
        non_existent = source_manager.get_sources_by_tier('non_existent_tier')
        assert non_existent == []
    
    def test_get_prioritized_sources(self, source_manager):
        """Test getting sources in priority order."""
        prioritized = source_manager.get_prioritized_sources()
        
        # Should have all sources
        assert len(prioritized) == 6
        
        # Check that tier_1 sources come first
        tier1_urls = source_manager.get_sources_by_tier('tier_1_premium')
        for url in tier1_urls:
            assert url in prioritized[:2]  # First 2 should be tier_1
    
    def test_get_source_count(self, source_manager):
        """Test getting total source count."""
        count = source_manager.get_source_count()
        assert count == 6
    
    def test_get_tier_info(self, source_manager):
        """Test getting source count by tier."""
        tier_info = source_manager.get_tier_info()
        
        assert tier_info['tier_1_premium'] == 2
        assert tier_info['tier_2_reliable'] == 2
        assert tier_info['tier_3_bulk'] == 2
        assert sum(tier_info.values()) == 6
    
    def test_validate_source_url(self, source_manager):
        """Test source URL validation."""
        # Valid URLs
        assert source_manager.validate_source_url('https://example.com/config.txt') is True
        assert source_manager.validate_source_url('http://example.com/config.txt') is True
        
        # Invalid URLs
        assert source_manager.validate_source_url('') is False
        assert source_manager.validate_source_url(None) is False
        assert source_manager.validate_source_url('ftp://example.com/config.txt') is False
        assert source_manager.validate_source_url('just text') is False
    
    def test_fallback_sources(self):
        """Test fallback sources when config file is missing."""
        with patch('os.path.exists', return_value=False):
            source_manager = SourceManager('non_existent_file.yaml')
            
            # Should have fallback sources
            assert 'emergency_fallback' in source_manager.sources
            fallback_urls = source_manager.get_sources_by_tier('emergency_fallback')
            assert len(fallback_urls) == 1
            assert 'mahdibland/V2RayAggregator' in fallback_urls[0]
    
    def test_yaml_import_error(self):
        """Test behavior when PyYAML is not available."""
        with patch.dict('sys.modules', {'yaml': None}):
            source_manager = SourceManager()
            
            # Should have fallback sources
            assert 'emergency_fallback' in source_manager.sources
            fallback_urls = source_manager.get_sources_by_tier('emergency_fallback')
            assert len(fallback_urls) == 1
    
    def test_malformed_yaml_handling(self):
        """Test handling of malformed YAML files."""
        with patch('builtins.open', mock_open(read_data='invalid: yaml: content: [')):
            source_manager = SourceManager('malformed.yaml')
            
            # Should have fallback sources due to YAML parsing error
            assert 'emergency_fallback' in source_manager.sources
    
    def test_empty_sources_handling(self):
        """Test handling of empty sources in config."""
        empty_config = {'sources': {}}
        
        with patch('yaml.safe_load', return_value=empty_config):
            source_manager = SourceManager('empty.yaml')
            
            # Should have fallback sources when no sources found
            assert 'emergency_fallback' in source_manager.sources
    
    def test_complex_nested_structure(self):
        """Test handling of complex nested YAML structures."""
        complex_config = {
            'sources': {
                'complex_tier': {
                    'level1': {
                        'level2': {
                            'urls': [
                                {'url': 'https://deep1.com/config1.txt'},
                                {'url': 'https://deep2.com/config2.txt'}
                            ]
                        }
                    }
                }
            }
        }
        
        with patch('yaml.safe_load', return_value=complex_config):
            source_manager = SourceManager('complex.yaml')
            
            # Should extract URLs from deep nesting
            urls = source_manager.get_sources_by_tier('complex_tier')
            assert len(urls) == 2
            assert 'https://deep1.com/config1.txt' in urls
            assert 'https://deep2.com/config2.txt' in urls
