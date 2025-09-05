"""
StreamlineVPN Setup
===================

Setup script for StreamlineVPN package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="streamline-vpn",
    version="2.0.0",
    author="StreamlineVPN Team",
    author_email="team@streamlinevpn.io",
    description="Enterprise VPN configuration aggregator with advanced features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/streamlinevpn/streamline-vpn",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Networking",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.7.0",
        ],
        "ml": [
            "scikit-learn>=1.3.0",
            "joblib>=1.3.0",
        ],
        "geo": [
            "geoip2>=4.7.0",
        ],
        "discovery": [
            "asyncpraw>=7.7.0",
            "telethon>=1.30.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "streamline-vpn=streamline_vpn.__main__:cli_main",
        ],
    },
    include_package_data=True,
    package_data={
        "streamline_vpn": ["config/*.yaml", "config/*.yml"],
    },
    keywords="vpn, proxy, configuration, aggregator, networking, security",
    project_urls={
        "Bug Reports": "https://github.com/streamlinevpn/streamline-vpn/issues",
        "Source": "https://github.com/streamlinevpn/streamline-vpn",
        "Documentation": "https://docs.streamlinevpn.io",
    },
)
