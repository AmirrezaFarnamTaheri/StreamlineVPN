"""
Content generators for various project files.
"""

from typing import Dict, Any


class ContentGenerators:
    """Generates content for various project files."""
    
    @staticmethod
    def get_run_unified_content() -> str:
        """Generate content for run_unified.py."""
        return '''#!/usr/bin/env python3
"""
Unified StreamlineVPN Runner
============================

Main entry point that starts all services (API, Web, CLI) in a unified manner.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.api.unified_api import UnifiedAPIServer
from streamline_vpn.web.static_server import StaticServer
from streamline_vpn.cli import main as cli_main


async def run_unified():
    """Run all services in unified mode."""
    print("🚀 Starting StreamlineVPN Unified Server...")
    
    # Start API server
    api_server = UnifiedAPIServer()
    api_task = asyncio.create_task(api_server.start())
    
    # Start web server
    web_server = StaticServer()
    web_task = asyncio.create_task(web_server.start())
    
    print("✅ All services started successfully!")
    print("🌐 API Server: http://localhost:8000")
    print("🌐 Web Interface: http://localhost:8080")
    print("💻 CLI available via: python -m streamline_vpn")
    
    try:
        await asyncio.gather(api_task, web_task)
    except KeyboardInterrupt:
        print("\\n🛑 Shutting down services...")
        await api_server.stop()
        await web_server.stop()
        print("✅ Shutdown complete")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        # Run CLI mode
        cli_main()
    else:
        # Run unified server
        asyncio.run(run_unified())


if __name__ == "__main__":
    main()
'''
    
    @staticmethod
    def get_run_api_content() -> str:
        """Generate content for run_api.py."""
        return '''#!/usr/bin/env python3
"""
StreamlineVPN API Runner
========================

Standalone API server runner.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.api.unified_api import UnifiedAPIServer


async def run_api():
    """Run API server only."""
    print("🚀 Starting StreamlineVPN API Server...")
    
    server = UnifiedAPIServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\\n🛑 Shutting down API server...")
        await server.stop()
        print("✅ Shutdown complete")


def main():
    """Main entry point."""
    asyncio.run(run_api())


if __name__ == "__main__":
    main()
'''
    
    @staticmethod
    def get_run_web_content() -> str:
        """Generate content for run_web.py."""
        return '''#!/usr/bin/env python3
"""
StreamlineVPN Web Runner
========================

Standalone web interface runner.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.web.static_server import StaticServer


async def run_web():
    """Run web server only."""
    print("🚀 Starting StreamlineVPN Web Interface...")
    
    server = StaticServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\\n🛑 Shutting down web server...")
        await server.stop()
        print("✅ Shutdown complete")


def main():
    """Main entry point."""
    asyncio.run(run_web())


if __name__ == "__main__":
    main()
'''
    
    @staticmethod
    def get_main_js_content() -> str:
        """Generate content for main.js."""
        return '''/**
 * StreamlineVPN Web Interface - Main JavaScript
 * ============================================
 */

class StreamlineVPNApp {
    constructor() {
        this.apiBase = '/api';
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('nav a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo(link.getAttribute('href'));
            });
        });
        
        // Form submissions
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmit(form);
            });
        });
    }
    
    async loadInitialData() {
        try {
            const response = await fetch(`${this.apiBase}/health`);
            const data = await response.json();
            this.updateStatus(data);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to connect to server');
        }
    }
    
    async navigateTo(path) {
        // Simple SPA navigation
        const content = document.getElementById('main-content');
        content.innerHTML = '<div class="loading">Loading...</div>';
        
        try {
            const response = await fetch(path);
            const html = await response.text();
            content.innerHTML = html;
        } catch (error) {
            content.innerHTML = '<div class="error">Page not found</div>';
        }
    }
    
    async handleFormSubmit(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        
        try {
            const response = await fetch(form.action, {
                method: form.method || 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            this.showSuccess('Operation completed successfully');
        } catch (error) {
            this.showError('Operation failed: ' + error.message);
        }
    }
    
    updateStatus(data) {
        const statusElement = document.getElementById('status');
        if (statusElement) {
            statusElement.textContent = data.status || 'Unknown';
        }
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new StreamlineVPNApp();
});
'''
    
    @staticmethod
    def get_sources_yaml_content() -> str:
        """Generate content for sources.yaml."""
        return '''# StreamlineVPN Sources Configuration
# =============================================

sources:
  # Example VPN sources - replace with actual sources
  - name: "Example Source 1"
    url: "https://example.com/vpn-configs.txt"
    type: "http"
    enabled: true
    priority: 1
    refresh_interval: 3600  # 1 hour
    timeout: 30
    retry_attempts: 3
    
  - name: "Example Source 2"
    url: "https://another-example.com/configs.json"
    type: "http"
    enabled: true
    priority: 2
    refresh_interval: 7200  # 2 hours
    timeout: 30
    retry_attempts: 3

# Global settings
global_settings:
  max_concurrent_sources: 10
  default_timeout: 30
  default_retry_attempts: 3
  cache_duration: 3600
  enable_compression: true
  user_agent: "StreamlineVPN/1.0.0"
  
# Filtering rules
filters:
  include_patterns:
    - "*.ovpn"
    - "*.conf"
    - "*.json"
  
  exclude_patterns:
    - "*.tmp"
    - "*.bak"
    - "*test*"
  
  min_file_size: 100  # bytes
  max_file_size: 1048576  # 1MB

# Output settings
output:
  format: "unified"
  compression: true
  deduplication: true
  validation: true
  backup_enabled: true
  backup_count: 5
'''
    
    @staticmethod
    def get_env_example_content() -> str:
        """Generate content for .env.example."""
        return '''# StreamlineVPN Environment Configuration
# =============================================

# Database Configuration
DATABASE_URL=sqlite:///streamline_vpn.db
# For PostgreSQL: postgresql://user:password@localhost/streamline_vpn
# For MySQL: mysql://user:password@localhost/streamline_vpn

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
# For Redis Cluster: redis://node1:6379,node2:6379,node3:6379

# API Configuration
API_KEY=your-secret-api-key-here
SECRET_KEY=your-secret-key-for-sessions
JWT_SECRET=your-jwt-secret-key

# Server Configuration
HOST=0.0.0.0
API_PORT=8000
WEB_PORT=8080
DEBUG=false
LOG_LEVEL=INFO

# Security Configuration
ENCRYPTION_KEY=your-encryption-key-32-chars
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30

# Cache Configuration
CACHE_TTL=3600
CACHE_MAX_SIZE=1000
ENABLE_L1_CACHE=true
ENABLE_L2_CACHE=true
ENABLE_L3_CACHE=true

# External Services
EXTERNAL_API_TIMEOUT=30
EXTERNAL_API_RETRIES=3
ENABLE_PROXY=false
PROXY_URL=

# Development Settings
DEVELOPMENT_MODE=false
ENABLE_DEBUG_TOOLBAR=false
AUTO_RELOAD=false
'''
    
    @staticmethod
    def get_pyproject_toml_content() -> str:
        """Generate content for pyproject.toml."""
        return '''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "streamline-vpn"
version = "1.0.0"
description = "StreamlineVPN - Advanced VPN Configuration Manager"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "StreamlineVPN Team", email = "team@streamlinevpn.com"}
]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
requires-python = ">=3.8"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "aiohttp>=3.9.0",
    "pydantic>=2.5.0",
    "click>=8.1.0",
    "pyyaml>=6.0.1",
    "redis>=5.0.0",
    "aioredis>=2.0.1",
    "sqlalchemy>=2.0.0",
    "alembic>=1.13.0",
    "structlog>=23.2.0",
    "prometheus-client>=0.19.0",
    "python-multipart>=0.0.6",
    "jinja2>=3.1.0",
    "aiofiles>=23.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.7.0",
    "pre-commit>=3.5.0",
]
test = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.25.0",
    "pytest-mock>=3.12.0",
]

[project.urls]
Homepage = "https://github.com/streamlinevpn/streamline-vpn"
Documentation = "https://docs.streamlinevpn.com"
Repository = "https://github.com/streamlinevpn/streamline-vpn.git"
"Bug Tracker" = "https://github.com/streamlinevpn/streamline-vpn/issues"

[project.scripts]
streamline-vpn = "streamline_vpn.cli:main"
streamline-vpn-api = "streamline_vpn.api.unified_api:main"
streamline-vpn-web = "streamline_vpn.web.static_server:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
"streamline_vpn" = ["web/static/*", "web/templates/*"]

[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["streamline_vpn"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]

[tool.coverage.run]
source = ["src/streamline_vpn"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
    "*/migrations/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
'''
    
    @staticmethod
    def get_requirements_content() -> str:
        """Generate content for requirements.txt."""
        return '''# StreamlineVPN Production Dependencies
# =============================================

# Web Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
aiohttp>=3.9.0

# Data Validation & Serialization
pydantic>=2.5.0
pyyaml>=6.0.1

# CLI Framework
click>=8.1.0

# Database & Caching
redis>=5.0.0
aioredis>=2.0.1
sqlalchemy>=2.0.0
alembic>=1.13.0

# Logging & Monitoring
structlog>=23.2.0
prometheus-client>=0.19.0

# HTTP & File Handling
python-multipart>=0.0.6
aiofiles>=23.2.0

# Templates
jinja2>=3.1.0

# Security
cryptography>=41.0.0
passlib[bcrypt]>=1.7.4

# Utilities
python-dotenv>=1.0.0
httpx>=0.25.0
'''
    
    @staticmethod
    def get_requirements_dev_content() -> str:
        """Generate content for requirements-dev.txt."""
        return '''# StreamlineVPN Development Dependencies
# =============================================

# Include production dependencies
-r requirements.txt

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
httpx>=0.25.0

# Code Quality
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.7.0

# Development Tools
pre-commit>=3.5.0
ipython>=8.17.0
jupyter>=1.0.0

# Documentation
mkdocs>=1.5.0
mkdocs-material>=9.4.0
mkdocstrings[python]>=0.24.0

# Performance Testing
locust>=2.17.0
memory-profiler>=0.61.0

# Security Testing
bandit>=1.7.0
safety>=2.3.0
'''
