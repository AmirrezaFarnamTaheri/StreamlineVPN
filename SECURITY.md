# Security Policy

This project fetches and processes third-party VPN subscription feeds. **All inbound data is treated as untrusted** and subject to comprehensive validation and sanitization.

## Security Overview

CleanConfigs SubMerger implements a defense-in-depth security model with multiple layers of protection:

### Data Validation & Sanitization
- **Input validation**: All hostnames, ports, and URLs are validated before any connection attempt
- **Content filtering**: Malicious patterns and suspicious content are automatically detected and filtered
- **Protocol validation**: Only supported VPN protocols are processed
- **Size limits**: Strict limits on configuration size and content length

### File System Security
- **Path validation**: All output paths are validated to prevent directory traversal attacks
- **Atomic writes**: File operations are atomic with rollback on error
- **Safe deserialization**: YAML files are loaded using `yaml.safe_load()` only
- **Permission checks**: Proper file permissions are enforced

### Network Security
- **TLS enforcement**: Certificate checks and hostname verification are never disabled
- **Rate limiting**: Per-host rate limiting prevents abuse and resource exhaustion
- **Circuit breakers**: Automatic failure detection and recovery
- **Timeout controls**: Bounded request timeouts prevent hanging connections

### API Security
- **Authentication**: REST endpoints can be protected with API tokens via `API_TOKEN` environment variable
- **Rate limiting**: Per-IP rate limiting for public endpoints (default: 100 requests/minute)
- **Input sanitization**: All API inputs are validated and sanitized
- **CORS protection**: Configurable CORS policies for web access

### Resource Protection
- **Concurrency limits**: Bounded concurrency prevents resource exhaustion
- **Memory management**: Strict memory limits and garbage collection
- **CPU throttling**: Automatic backoff under high load
- **Disk space monitoring**: Output directory size monitoring

## Threat Model

### Identified Threats
1. **Malicious VPN configurations**: Trojan horses, backdoors, or compromised endpoints
2. **Data exfiltration**: Attempts to steal or leak processed data
3. **Resource exhaustion**: DoS attacks via excessive resource consumption
4. **Path traversal**: Attempts to access files outside designated directories
5. **Code injection**: Malicious code in configuration files
6. **Network attacks**: Man-in-the-middle, DNS poisoning, etc.

### Mitigation Strategies
- **Zero-trust validation**: All inputs validated regardless of source
- **Sandboxed processing**: Isolated execution environments
- **Comprehensive logging**: Audit trails for all operations
- **Regular updates**: Security patches and dependency updates
- **Monitoring**: Real-time threat detection and alerting

## Security Configuration

### Environment Variables
```bash
# API Security
API_TOKEN=your-secure-token-here
RATE_LIMIT_PER_MINUTE=100

# Network Security
VPN_TIMEOUT=30
VPN_MAX_RETRIES=3
VPN_CONCURRENT_LIMIT=50

# Content Security
MAX_CONFIG_SIZE=1048576  # 1MB
ALLOWED_PROTOCOLS=vmess,vless,trojan,shadowsocks
```

### Security Headers
The API includes security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`

## Vulnerability Reporting

### How to Report
We take security vulnerabilities seriously. Please report them responsibly:

1. **Public disclosure**: Open a GitHub issue with a minimal proof-of-concept
2. **Private disclosure**: Contact maintainers directly for sensitive issues
3. **Include details**: Provide steps to reproduce, affected versions, and impact assessment

### Response Timeline
- **Acknowledgment**: Within 24 hours
- **Initial assessment**: Within 72 hours
- **Patch for critical issues**: Within 7 days
- **Public disclosure**: Coordinated with patch release

### Security Contact
- **GitHub Issues**: For public security discussions
- **Email**: [security@cleanconfigs.com] (for private disclosures)
- **PGP Key**: Available upon request for encrypted communications

## Security Best Practices

### For Users
1. **Keep updated**: Always use the latest version
2. **Secure configuration**: Use strong API tokens and secure network settings
3. **Monitor logs**: Regularly review logs for suspicious activity
4. **Network security**: Deploy behind firewalls and use VPNs when appropriate
5. **Access control**: Limit API access to trusted networks only

### For Developers
1. **Code review**: All security-related changes require review
2. **Testing**: Comprehensive security testing before releases
3. **Dependencies**: Regular security audits of dependencies
4. **Documentation**: Security implications documented for all features
5. **Incident response**: Clear procedures for security incidents

## Compliance & Standards

- **OWASP Top 10**: Protection against common web vulnerabilities
- **CVE tracking**: Monitoring and patching of known vulnerabilities
- **Security headers**: Implementation of recommended security headers
- **Logging standards**: Structured logging for security monitoring
- **Access controls**: Principle of least privilege

## Security Updates

Security updates are released as needed. Subscribe to security advisories:
- **GitHub releases**: Tagged with security labels
- **Security mailing list**: For critical updates
- **RSS feed**: For automated monitoring

---

**Note**: This security policy is regularly reviewed and updated. Last updated: [Current Date]

