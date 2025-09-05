import re
from typing import Dict, Any, List, Set
from urllib.parse import urlparse
from ...settings import get_settings


def analyze_domain_info(url: str, blocked_domains: Set[str]) -> Dict[str, Any]:
    try:
        settings = get_settings()
        parsed = urlparse(url)
        domain = parsed.hostname or ""
        is_blocked = any(b in domain for b in blocked_domains)
        has_suspicious_tld = any(domain.endswith(t) for t in settings.security.suspicious_tlds)
        is_ip = bool(re.match(r"^\d+\.\d+\.\d+\.\d+$", domain))
        return {
            "domain": domain,
            "is_blocked": is_blocked,
            "has_suspicious_tld": has_suspicious_tld,
            "is_ip": is_ip,
            "is_safe": not is_blocked and not has_suspicious_tld,
        }
    except Exception as e:
        return {
            "domain": "",
            "is_blocked": True,
            "has_suspicious_tld": False,
            "is_ip": False,
            "is_safe": False,
            "error": str(e),
        }


def analyze_urls_in_text(
    text: str,
    blocked_domains: Set[str],
    validator,
) -> Dict[str, List[str]]:
    # crude URL detection
    url_pattern = r"https?://[^\s'\"]+"
    urls = re.findall(url_pattern, text)
    suspicious: List[str] = []
    blocked: List[str] = []
    valid: List[str] = []

    for u in urls:
        if any(b in u for b in blocked_domains):
            blocked.append(u)
            continue
        if validator and not validator.validate_url(u):
            suspicious.append(u)
            continue
        valid.append(u)

    return {
        "valid_urls": valid,
        "suspicious_urls": suspicious,
        "blocked_urls": blocked,
    }
