# Troubleshooting Guide

## Common Issues and Solutions

### Configuration Issues

#### No Sources Loading
**Problem**: Application shows 0 sources or fails to load configuration
**Solutions**:
- Ensure `config/sources.yaml` exists and has valid YAML syntax
- Check file permissions: `ls -la config/sources.yaml`
- Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('config/sources.yaml'))"`
- Verify source URLs are accessible: `python -m streamline_vpn --config config/sources.yaml --dry-run`

#### Configuration File Not Found
**Problem**: Error "Config file not found, using fallback sources"
**Solutions**:
- Check file path: `config/sources.yaml`
- Verify file exists: `ls -la config/`
- Check working directory when running the application
- Use absolute path if needed: `python -m streamline_vpn --config /full/path/sources.yaml`

### Import and Dependency Issues

#### Module Import Errors
**Problem**: `ImportError: cannot import name 'SourceManager'`
**Solutions**:
- Ensure you're running from the project root directory
- Check Python version: `python --version` (requires Python 3.8+)
- Install dependencies: `pip install -r requirements.txt`
- Verify project is set up correctly and `python -m streamline_vpn --help` works

#### Missing Dependencies
**Problem**: `ModuleNotFoundError` for aiohttp, yaml, etc.
**Solutions**:
- Install core dependencies: `pip install -r requirements.txt`
- Check virtual environment activation
- Verify pip installation: `pip list | findstr aiohttp` (Windows) or `pip list | grep aiohttp` (Unix)

### Runtime Issues

#### No Output Generated
**Problem**: Application runs but no output files are created
**Solutions**:
- Check output directory permissions: `ls -la output/`
- Verify pipeline via API: `POST /api/v1/pipeline/run`
- Check network connectivity to source URLs
- Review log file: `tail -f streamline_vpn.log`

#### Application Hangs or Freezes
**Problem**: Application appears to freeze during execution
**Solutions**:
- Check network connectivity
- Reduce concurrency via settings or env
- Increase timeout via settings or env
- Monitor system resources: CPU, memory, network

#### Memory Issues
**Problem**: Application crashes with memory errors
**Solutions**:
- Reduce concurrent processing: `--concurrent 20`
- Process sources in smaller batches
- Monitor memory usage during execution
- Check for memory leaks in long-running processes

### Network and Connectivity Issues

#### Source Validation Failures
**Problem**: All sources show as inaccessible (0/32 accessible)
**Solutions**:
- Check network connectivity: `ping google.com`
- Verify firewall settings
- Check proxy configuration if using corporate network
- Test individual sources manually in browser
- Run a dry-run to test source accessibility: `python -m streamline_vpn --config config/sources.yaml --dry-run`

#### Timeout Errors
**Problem**: Requests timing out during source processing
**Solutions**:
- Increase timeout: `--timeout 60`
- Check network latency to source servers
- Reduce concurrent requests: `--concurrent 20`
- Verify DNS resolution: `nslookup source-domain.com`

### Performance Issues

#### Slow Processing
**Problem**: Application takes too long to process sources
**Solutions**:
- Adjust concurrency: `--concurrent 50`
- Check network bandwidth and latency
- Optimize source tier organization
- Prefer faster sources in Tier 1
- Monitor system resources during execution

#### High Memory Usage
**Problem**: Application uses excessive memory
**Solutions**:
- Reduce concurrent processing
- Process sources in smaller batches
- Monitor memory usage with `htop` or `top`
- Check for memory leaks in long-running processes

### Testing Issues

#### Test Failures
**Problem**: Tests fail with various errors
**Solutions**:
- Run tests individually: `pytest -q tests/test_core.py -v`
- Check test dependencies: `pip install -r requirements-dev.txt`
- Verify Python environment: `python --version`
- Check test configuration: `type pytest.ini` (Windows) or `cat pytest.ini`

#### Coverage Issues
**Problem**: Test coverage below required threshold
**Solutions**:
- Run coverage locally: `pytest -q --cov=src --cov-report=html`
- Review coverage report: open `htmlcov/index.html`
- Add tests for uncovered code paths
- Check test file organization and imports

## Environment Variables (common)

```bash
# Source configuration
STREAMLINE_VPN_CONFIG=config/sources.yaml

# Processing settings
STREAMLINE_VPN_CONCURRENT_LIMIT=50
STREAMLINE_VPN_TIMEOUT=30
STREAMLINE_VPN_MAX_RETRIES=3

# Output settings
STREAMLINE_VPN_OUTPUT_DIR=output
```

## Debug Commands

### Basic Diagnostics
```bash
# Check Python environment
python --version
pip list

# Validate configuration structure
python -c "import yaml; yaml.safe_load(open('config/sources.yaml'))"

# Test module import
python -c "import streamline_vpn; print('✅ imports OK')"

# Quick source count (API required for full details)
python -m streamline_vpn --config config/sources.yaml --dry-run
```

### Network Diagnostics
```bash
# Test network connectivity
ping google.com
curl -I https://google.com

# Check DNS resolution
nslookup raw.githubusercontent.com
```

### Performance Diagnostics
```bash
# Monitor system resources
htop
```

## Log Analysis

### Common Log Messages
```
INFO - Starting merge with X sources
INFO - Merge completed: X valid configs from Y sources
WARNING - Source not accessible: URL
ERROR - Error processing source URL: Error message
```

### Debug Logging
```bash
# Enable debug logging
set STREAMLINE_VPN_LOG_LEVEL=DEBUG  # Windows
# or
export STREAMLINE_VPN_LOG_LEVEL=DEBUG  # Unix

# Monitor log file
tail -f streamline_vpn.log
```

## Getting Help

### Self-Diagnosis
1. Check logs in `logs/`
2. Validate configuration
3. Test imports
4. Check dependencies
5. Monitor resources

### Common Solutions
1. Restart application
2. Check file permissions
3. Verify network
4. Reduce concurrency
5. Increase timeouts

### When to Seek Help
- Application crashes consistently
- All sources fail validation
- Performance is significantly degraded
- Memory usage is excessive
- Tests fail consistently

### Support Resources
- Project issues: repository issue tracker
- Documentation: this troubleshooting guide and other docs pages
- Configuration: see `docs/configuration/`

## Deployment Issues

See deployment guidance in `docs/DEPLOYMENT.md` for container/Kubernetes-specific tips (ports, mounts, readiness probes, and service access).

