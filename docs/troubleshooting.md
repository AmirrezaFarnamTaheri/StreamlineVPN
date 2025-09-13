# Troubleshooting Guide

## Common Issues and Solutions

### Configuration Issues

#### No Sources Loading
**Problem**: Application shows 0 sources or fails to load configuration
**Solutions**:
- Ensure `config/sources.yaml` exists and has valid YAML syntax
- Check file permissions: `ls -la config/sources.yaml`
- Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('config/sources.yaml'))"`
- Verify source URLs are accessible: `python vpn_merger_main.py --validate`

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
- Install core dependencies: `pip install aiohttp PyYAML tqdm`
- Install all dependencies: `pip install -r requirements.txt`
- Check virtual environment activation
- Verify pip installation: `pip list | grep aiohttp`

### Runtime Issues

#### No Output Generated
**Problem**: Application runs but no output files are created
**Solutions**:
- Check output directory permissions: `ls -la output/`
- Verify sources are accessible via the API pipeline: `POST /api/v1/pipeline/run`
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
- Use `--validate` flag to test source accessibility

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
- Increase concurrency: `--concurrent 100`
- Check network bandwidth and latency
- Optimize source tier organization
- Use faster sources in tier_1_premium
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
- Run tests individually: `python -m pytest tests/test_sources.py -v`
- Check test dependencies: `pip install pytest pytest-asyncio`
- Verify Python environment: `python --version`
- Check test configuration: `cat pytest.ini`

#### Coverage Issues
**Problem**: Test coverage below required threshold
**Solutions**:
- Run coverage locally: `python -m pytest --cov=vpn_merger --cov-report=html`
- Review coverage report: `open htmlcov/index.html`
- Add tests for uncovered code paths
- Check test file organization and imports

## Environment Variables

### Core Configuration
```bash
# Source configuration
VPN_SOURCES_CONFIG=config/sources.yaml

# Processing settings
VPN_CONCURRENT_LIMIT=50
VPN_TIMEOUT=30
VPN_MAX_RETRIES=3

# Output settings
VPN_OUTPUT_DIR=output
VPN_WRITE_BASE64=true
VPN_WRITE_CSV=true
VPN_WRITE_JSON=true
```

### Debug and Testing
```bash
# Enable debug logging
VPN_LOG_LEVEL=DEBUG

# Skip network operations for testing
SKIP_NETWORK=1

# Enable discovery cache
ENABLE_DISCOVERY_CACHE=1

# Enable validation cache
ENABLE_VALIDATION_CACHE=1
```

### Performance Tuning
```bash
# Adjust concurrency
VPN_CONCURRENT_LIMIT=100

# Increase timeout
VPN_TIMEOUT=60

# Memory management
VPN_CHUNK_SIZE=2097152  # 2MB
VPN_BLOOM_FILTER_SIZE=2000000
```

## Debug Commands

### Basic Diagnostics
```bash
# Check Python environment
python --version
pip list

# Validate configuration
python -c "import yaml; yaml.safe_load(open('config/sources.yaml'))"

# Test imports
python -c "from streamline_vpn import *; print('✅ All imports successful')"

# Check sources
python -c "from streamline_vpn import SourceManager; sources = SourceManager(); print(f'Loaded {len(sources.get_all_sources())} sources')"
```

### Network Diagnostics
```bash
# Test network connectivity
ping google.com
curl -I https://google.com

# Test source accessibility
python vpn_merger_main.py --validate

# Check DNS resolution
nslookup raw.githubusercontent.com
```

### Performance Diagnostics
```bash
# Monitor system resources
htop
iotop
nethogs

# Check Python performance
python -m cProfile -o profile.stats vpn_merger_main.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
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
export VPN_LOG_LEVEL=DEBUG

# Run with verbose output
python vpn_merger_main.py --verbose

# Monitor log file
tail -f streamline_vpn.log
```

## Getting Help

### Self-Diagnosis
1. **Check logs**: Review `streamline_vpn.log` for error messages
2. **Validate configuration**: Use `--validate` flag to test sources
3. **Test imports**: Verify all modules can be imported
4. **Check dependencies**: Ensure all required packages are installed
5. **Monitor resources**: Check system CPU, memory, and network usage

### Common Solutions
1. **Restart application**: Clear any cached state
2. **Check file permissions**: Ensure configuration files are readable
3. **Verify network**: Test connectivity to external sources
4. **Reduce concurrency**: Lower concurrent processing limits
5. **Increase timeouts**: Allow more time for slow sources

### When to Seek Help
- Application crashes consistently
- All sources fail validation
- Performance is significantly degraded
- Memory usage is excessive
- Tests fail consistently

### Support Resources
- **Project Issues**: Create an issue in the project repository
- **Documentation**: Review this troubleshooting guide and other docs
- **Configuration**: Check `docs/configuration/` for setup details
- **Testing**: Use `scripts/run_tests.py` for comprehensive testing

## Prevention

### Best Practices
1. **Regular validation**: Run `--validate` regularly to check source health
2. **Monitor logs**: Review logs for warnings and errors
3. **Test changes**: Validate configuration changes before production
4. **Backup configuration**: Keep backup of working configurations
5. **Version control**: Commit all configuration changes

### Maintenance
1. **Update sources**: Regularly review and update source URLs
2. **Monitor performance**: Track processing times and resource usage
3. **Review logs**: Analyze logs for patterns and issues
4. **Test regularly**: Run tests to ensure system health
5. **Update dependencies**: Keep packages up to date

This troubleshooting guide covers the most common issues and solutions. For additional help, refer to the configuration guide or create an issue in the project repository.

