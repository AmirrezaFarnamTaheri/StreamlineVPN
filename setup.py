#!/usr/bin/env python3
"""
StreamlineVPN Setup Configuration
=================================

Advanced VPN Configuration Aggregator
A comprehensive tool for collecting, processing, and serving VPN configurations.
"""

import os
import sys
from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop

# Ensure we're using the right Python version
if sys.version_info < (3, 8):
    sys.exit("StreamlineVPN requires Python 3.8 or higher")

# Get the long description from README
def get_long_description():
    """Get the long description from README.md"""
    readme_path = Path(__file__).parent / "README.md"
    if readme_path.exists():
        return readme_path.read_text(encoding="utf-8")
    return "Advanced VPN Configuration Aggregator"

# Get version from __init__.py
def get_version():
    """Get version from streamline_vpn/__init__.py"""
    init_path = Path(__file__).parent / "src" / "streamline_vpn" / "__init__.py"
    if init_path.exists():
        with open(init_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "2.0.0"

# Custom install command to create necessary directories
class CustomInstall(install):
    """Custom install command to create necessary directories"""
    
    def run(self):
        super().run()
        self.create_directories()
    
    def create_directories(self):
        """Create necessary directories after installation"""
        base_dir = Path(self.install_lib) / "streamline_vpn"
        
        directories = [
            "data",
            "logs", 
            "output",
            "config",
            "cache"
        ]
        
        for directory in directories:
            dir_path = base_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")

# Custom develop command
class CustomDevelop(develop):
    """Custom develop command"""
    
    def run(self):
        super().run()
        self.create_directories()
    
    def create_directories(self):
        """Create necessary directories for development"""
        base_dir = Path(__file__).parent
        
        directories = [
            "data",
            "logs",
            "output", 
            "cache"
        ]
        
        for directory in directories:
            dir_path = base_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")

# Read requirements from requirements files
def get_requirements(env_type="prod"):
    """Get requirements from requirements files"""
    requirements = []
    
    # Base requirements
    req_files = {
        "prod": "requirements.txt",
        "dev": "requirements-dev.txt"
    }
    
    req_file = req_files.get(env_type, "requirements.txt")
    req_path = Path(__file__).parent / req_file
    
    if req_path.exists():
        with open(req_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-r"):
                    # Handle version constraints
                    if ">=" in line or "==" in line or "<=" in line or "~=" in line:
                        requirements.append(line)
                    else:
                        requirements.append(line)
    
    return requirements

# Package metadata
setup(
    name="streamline-vpn",
    version=get_version(),
    author="StreamlineVPN Team",
    author_email="team@streamlinevpn.com",
    description="Advanced VPN Configuration Aggregator",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/streamlinevpn/streamlinevpn",
    project_urls={
        "Bug Reports": "https://github.com/streamlinevpn/streamlinevpn/issues",
        "Documentation": "https://docs.streamlinevpn.com",
        "Source": "https://github.com/streamlinevpn/streamlinevpn",
        "Changelog": "https://github.com/streamlinevpn/streamlinevpn/blob/main/CHANGELOG.md",
    },
    
    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "streamline_vpn": [
            "config/*.yaml",
            "config/*.yml", 
            "config/*.json",
            "docs/**/*",
            "templates/**/*",
            "static/**/*",
            "*.md",
            "*.txt",
            "*.yml",
            "*.yaml"
        ]
    },
    
    # Entry points
    entry_points={
        "console_scripts": [
            "streamline-vpn=streamline_vpn.cli:main",
            "streamline-api=streamline_vpn.web.unified_api:main",
            "streamline-web=streamline_vpn.web.server:main",
        ],
        "streamline_vpn.plugins": [
            "basic=streamline_vpn.plugins.basic:BasicPlugin",
            "advanced=streamline_vpn.plugins.advanced:AdvancedPlugin",
        ],
    },
    
    # Dependencies
    install_requires=get_requirements("prod"),
    extras_require={
        "dev": get_requirements("dev"),
        "prod": get_requirements("prod"),
        "all": get_requirements("dev") + get_requirements("prod"),
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
        ],
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=1.3.0",
            "myst-parser>=2.0.0",
        ],
    },
    
    # Python version requirements
    python_requires=">=3.8",
    
    # Classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: System :: Networking",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Framework :: FastAPI",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    
    # Keywords
    keywords=[
        "vpn", "proxy", "configuration", "aggregator", "fastapi", 
        "streamline", "networking", "security", "privacy", "clash",
        "v2ray", "shadowsocks", "trojan", "vmess", "vless"
    ],
    
    # Custom commands
    cmdclass={
        "install": CustomInstall,
        "develop": CustomDevelop,
    },
    
    # Zip safe
    zip_safe=False,
    
    # Data files
    data_files=[
        ("streamline_vpn/config", [
            "config/sources.yaml",
            "config/environment.example",
        ]),
        ("streamline_vpn/docs", [
            "docs/api/index.html",
            "docs/api/websocket.html",
            "docs/troubleshooting.html",
        ]),
        ("streamline_vpn/scripts", [
            "scripts/comprehensive_validator.py",
            "scripts/final_validator.py",
            "scripts/postgres-init/01-init.sql",
        ]),
    ],
    
    # Options
    options={
        "build_sphinx": {
            "source_dir": "docs",
            "build_dir": "docs/_build",
            "config_dir": "docs",
        }
    },
    
    # Test suite
    test_suite="tests",
    
    # Include tests
    tests_require=get_requirements("dev"),
    
    # Platform support
    platforms=["any"],
    
    # Download URL
    download_url=f"https://github.com/streamlinevpn/streamlinevpn/archive/v{get_version()}.tar.gz",
)

# Post-installation message
def post_install_message():
    """Display post-installation message"""
    print("\n" + "="*60)
    print("🎉 StreamlineVPN installed successfully!")
    print("="*60)
    print("\n📚 Quick Start:")
    print("  1. Copy config/environment.example to .env")
    print("  2. Configure your settings in .env")
    print("  3. Run: streamline-vpn process")
    print("  4. Or start the API: streamline-api")
    print("  5. Or start the web interface: streamline-web")
    print("\n📖 Documentation:")
    print("  - API Docs: http://localhost:8080/docs")
    print("  - Web Interface: http://localhost:8000")
    print("  - GitHub: https://github.com/streamlinevpn/streamlinevpn")
    print("\n🔧 Configuration:")
    print("  - Sources: config/sources.yaml")
    print("  - Environment: .env")
    print("  - Output: output/")
    print("\n" + "="*60)

if __name__ == "__main__":
    post_install_message()