#!/usr/bin/env python3
"""
StreamlineVPN Installation Verification Script
==============================================

This script verifies that the StreamlineVPN package is properly installed
and all components are working correctly.
"""

import sys
import asyncio
from pathlib import Path

def test_imports():
    """Test all package imports."""
    print("🔍 Testing package imports...")
    
    try:
        # Test main package
        import streamline_vpn
        print("✅ Main package import successful")
        
        # Test core components
        from streamline_vpn.core import StreamlineVPNMerger, SourceManager, ConfigurationProcessor, OutputManager, CacheManager
        print("✅ Core components import successful")
        
        # Test models
        from streamline_vpn.models import VPNConfiguration, SourceMetadata, ProcessingResult
        print("✅ Data models import successful")
        
        # Test utilities
        from streamline_vpn.utils import setup_logging, validate_url, format_bytes
        print("✅ Utilities import successful")
        
        # Test ML components
        from streamline_vpn.ml import QualityPredictor
        print("✅ ML components import successful")
        
        # Test geo components
        from streamline_vpn.geo import GeographicOptimizer
        print("✅ Geographic components import successful")
        
        # Test discovery components
        from streamline_vpn.discovery import DiscoveryManager
        print("✅ Discovery components import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality."""
    print("\n🔍 Testing basic functionality...")
    
    try:
        from streamline_vpn import create_merger, merge_configurations
        from streamline_vpn.models.configuration import VPNConfiguration, ProtocolType
        
        # Test merger creation
        merger = create_merger("config/sources.yaml")
        print("✅ Merger creation successful")
        
        # Test VPN configuration creation
        config = VPNConfiguration(
            protocol=ProtocolType.VMESS,
            server="test.example.com",
            port=443,
            user_id="test-id"
        )
        print("✅ VPN configuration creation successful")
        
        # Test configuration validation
        assert config.is_valid, "Configuration should be valid"
        print("✅ Configuration validation successful")
        
        # Test configuration serialization
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict), "to_dict() should return dict"
        print("✅ Configuration serialization successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        return False

async def test_async_functionality():
    """Test async functionality."""
    print("\n🔍 Testing async functionality...")
    
    try:
        from streamline_vpn.core.merger import StreamlineVPNMerger
        
        # Test merger initialization
        merger = StreamlineVPNMerger()
        print("✅ Async merger initialization successful")
        
        # Test statistics retrieval
        stats = await merger.get_statistics()
        assert isinstance(stats, dict), "Statistics should be dict"
        print("✅ Statistics retrieval successful")
        
        # Test configuration retrieval
        configs = await merger.get_configurations()
        assert isinstance(configs, list), "Configurations should be list"
        print("✅ Configuration retrieval successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Async functionality test error: {e}")
        return False

def test_file_structure():
    """Test file structure."""
    print("\n🔍 Testing file structure...")
    
    required_files = [
        "src/streamline_vpn/__init__.py",
        "src/streamline_vpn/__main__.py",
        "src/streamline_vpn/core/__init__.py",
        "src/streamline_vpn/core/merger.py",
        "src/streamline_vpn/core/source_manager.py",
        "src/streamline_vpn/core/config_processor.py",
        "src/streamline_vpn/core/output_manager.py",
        "src/streamline_vpn/core/cache_manager.py",
        "src/streamline_vpn/models/__init__.py",
        "src/streamline_vpn/models/configuration.py",
        "src/streamline_vpn/models/source.py",
        "src/streamline_vpn/models/processing_result.py",
        "src/streamline_vpn/utils/__init__.py",
        "src/streamline_vpn/utils/logging.py",
        "src/streamline_vpn/utils/validation.py",
        "src/streamline_vpn/utils/helpers.py",
        "src/streamline_vpn/ml/__init__.py",
        "src/streamline_vpn/ml/quality_predictor.py",
        "src/streamline_vpn/geo/__init__.py",
        "src/streamline_vpn/geo/optimizer.py",
        "src/streamline_vpn/discovery/__init__.py",
        "src/streamline_vpn/discovery/manager.py",
        "config/sources.yaml",
        "requirements.txt",
        "setup.py",
        "README.md",
        "LICENSE",
        ".gitignore"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_documentation():
    """Test documentation completeness."""
    print("\n🔍 Testing documentation...")
    
    try:
        # Test README
        readme_path = Path("README.md")
        if readme_path.exists():
            readme_content = readme_path.read_text(encoding='utf-8')
            required_sections = [
                "# StreamlineVPN",
                "## 🚀 Features",
                "## 📦 Installation",
                "## 🎯 Quick Start",
                "## 🏗️ Architecture"
            ]
            
            for section in required_sections:
                if section not in readme_content:
                    print(f"❌ Missing README section: {section}")
                    return False
            
            print("✅ README documentation complete")
        else:
            print("❌ README.md not found")
            return False
        
        # Test package docstrings
        import streamline_vpn
        if not streamline_vpn.__doc__:
            print("❌ Package missing docstring")
            return False
        
        print("✅ Package documentation complete")
        return True
        
    except Exception as e:
        print(f"❌ Documentation test error: {e}")
        return False

async def main():
    """Run all verification tests."""
    print("🚀 StreamlineVPN Installation Verification")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Package Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Async Functionality", test_async_functionality),
        ("Documentation", test_documentation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! StreamlineVPN is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
