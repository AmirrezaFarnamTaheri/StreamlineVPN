#!/usr/bin/env python3
"""
Comprehensive Project Validator
===============================

Runs a suite of structural, configuration, docs, and deployment checks and
prints a concise report. This is a pragmatic, self‑contained implementation
aligned with the analysis report’s intent while keeping maintenance light.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


@dataclass
class CheckResult:
    name: str
    status: str = "passed"  # passed | failed
    issues: List[Dict[str, Any]] = field(default_factory=list)

    def error(self, description: str, **extra: Any) -> None:
        self.issues.append({"severity": "error", "description": description, **extra})
        self.status = "failed"

    def warn(self, description: str, **extra: Any) -> None:
        self.issues.append({"severity": "warning", "description": description, **extra})

    def info(self, description: str, **extra: Any) -> None:
        self.issues.append({"severity": "info", "description": description, **extra})


def _exists(p: Path) -> bool:
    return p.exists()


def check_structure(root: Path) -> CheckResult:
    res = CheckResult("Project Structure")
    required_dirs = [
        "src/streamline_vpn",
        "src/streamline_vpn/web",
        "src/streamline_vpn/core",
        "docs",
        "docs/assets/css",
        "docs/assets/js",
        "config",
        "tests",
    ]
    for d in required_dirs:
        if not _exists(root / d):
            res.error(f"Missing required directory: {d}", path=d)

    required_files = [
        "run_unified.py",
        "run_api.py",
        "run_web.py",
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "docs/index.html",
        "docs/interactive.html",
        "docs/config_generator.html",
        "docs/troubleshooting.html",
        "docs/api-base.js",
        "docs/assets/js/main.js",
        "docs/assets/css/style.css",
        "config/sources.yaml",
    ]
    for f in required_files:
        if not _exists(root / f):
            res.error(f"Missing required file: {f}", path=f)
    return res


def check_runners(root: Path) -> CheckResult:
    res = CheckResult("Runner Scripts")
    for name in ["run_unified.py", "run_api.py", "run_web.py"]:
        p = root / name
        if not p.exists():
            res.error(f"Runner missing: {name}", file=name)
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            for pat in [r"def\s+main\(", r"__name__\s*==\s*['\"]__main__['\"]"]:
                if not re.search(pat, content):
                    res.warn(f"Runner may be incomplete: missing pattern {pat}", file=name)
        except Exception as exc:
            res.warn(f"Unable to read {name}: {exc}")
    return res


def check_docs_frontend(root: Path) -> CheckResult:
    res = CheckResult("Docs & Frontend")
    # api-base.js should include basic methods
    api = root / "docs" / "api-base.js"
    if api.exists():
        txt = api.read_text(encoding="utf-8", errors="replace")
        for token in ["window.API", "get:", "post:", "url:"]:
            if token not in txt:
                res.error(f"api-base.js missing token: {token}")
    else:
        res.error("docs/api-base.js missing")

    # main.js should reference init/update
    main = root / "docs" / "assets" / "js" / "main.js"
    if main.exists():
        txt = main.read_text(encoding="utf-8", errors="replace")
        for token in ["class StreamlineVPNApp", "init", "updateStatistics"]:
            if token not in txt:
                res.warn(f"main.js missing token: {token}")
    else:
        res.error("docs/assets/js/main.js missing")
    return res


def check_sources_yaml(root: Path) -> CheckResult:
    res = CheckResult("sources.yaml")
    cfg = root / "config" / "sources.yaml"
    if not cfg.exists():
        res.error("config/sources.yaml missing")
        return res
    if yaml is None:
        res.warn("PyYAML not available; skipping deep validation")
        return res
    try:
        data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            res.error("sources.yaml must be a mapping at top level")
            return res

        if "sources" not in data:
            res.error("'sources' key missing in sources.yaml")
            return res

        # Count sources across tiers; support both 'sources' (preferred) and 'urls' (legacy)
        total = 0
        tiers = (data.get("sources", {}) or {})
        if isinstance(tiers, dict):
            for tier in tiers.values():
                if not isinstance(tier, dict):
                    continue
                tier_sources = tier.get("sources")
                tier_urls = tier.get("urls")
                if isinstance(tier_sources, list):
                    total += len(tier_sources)
                elif isinstance(tier_urls, list):
                    total += len(tier_urls)
        if total < 5:
            res.warn(f"Only {total} sources configured; consider adding more")
    except Exception as exc:
        res.error(f"Failed to parse sources.yaml: {exc}")
    return res


def check_api_docs(root: Path) -> CheckResult:
    res = CheckResult("API Documentation")
    page = root / "docs" / "api" / "index.html"
    if not page.exists():
        res.error("docs/api/index.html missing")
        return res
    txt = page.read_text(encoding="utf-8", errors="replace")
    for section in ["Authentication", "Endpoints", "Error Codes", "Rate Limits", "Examples"]:
        if section not in txt:
            res.warn(f"API docs missing section: {section}")
    for code in ["INSUFFICIENT_PERMISSIONS", "SERVICE_UNAVAILABLE"]:
        if code not in txt:
            res.warn(f"API docs should include error code: {code}")
    return res


def check_deployment(root: Path) -> CheckResult:
    res = CheckResult("Deployment")
    # Ensure core Docker and Nginx files exist
    for f in ["docker-compose.yml", "docker-compose.production.yml", "Dockerfile"]:
        if not _exists(root / f):
            res.warn(f"Deployment file missing: {f}")
    if not _exists(root / "config" / "nginx" / "nginx.conf"):
        res.warn("Nginx config missing: config/nginx/nginx.conf")
    return res


def run_checks(root: Path) -> Dict[str, Any]:
    checks = [
        check_structure,
        check_runners,
        check_docs_frontend,
        check_sources_yaml,
        check_api_docs,
        check_deployment,
    ]
    results: Dict[str, Any] = {"checks": {}, "summary": {}}
    failed = 0
    warnings = 0

    for fn in checks:
        res = fn(root)
        results["checks"][res.name] = {
            "status": res.status,
            "issues": res.issues,
        }
        if res.status != "passed":
            failed += 1
        for issue in res.issues:
            if issue.get("severity") == "warning":
                warnings += 1

    results["summary"] = {
        "total_checks": len(checks),
        "failed": failed,
        "warnings": warnings,
        "passed": len(checks) - failed,
        "status": "PASS" if failed == 0 else ("NEEDS_ATTENTION" if failed < len(checks) else "FAIL"),
    }
    return results

def _supports_unicode() -> bool:
    try:
        "✓".encode(sys.stdout.encoding or "utf-8", errors="strict")
        return True
    except Exception:
        return False

def print_report_win_safe(results: Dict[str, Any]) -> None:
    s = results["summary"]
    use_unicode = _supports_unicode()
    pass_icon = "✅" if use_unicode else "PASS"
    fail_icon = "❌" if use_unicode else "FAIL"
    warn_icon = "⚠️" if use_unicode else "WARN"

    print("# StreamlineVPN Project Validation Report\n")
    print("Summary:")
    print(f"- Checks: {s['total_checks']}")
    print(f"- Passed: {s['passed']}")
    print(f"- Failed: {s['failed']}")
    print(f"- Warnings: {s['warnings']}")
    overall = s.get('status', 'NEEDS_ATTENTION')
    overall_mark = pass_icon if overall == 'PASS' else (fail_icon if overall == 'FAIL' else warn_icon)
    print(f"- Overall: {overall} {overall_mark}")
    print()

    for name, data in results["checks"].items():
        icon = pass_icon if data.get("status") == "passed" else fail_icon
        print(f"## {icon} {name}")
        issues = data.get("issues", [])
        if not issues:
            print("- No issues found\n")
            continue
        for issue in issues:
            sev = issue.get("severity", "info").upper()
            desc = issue.get("description", "")
            file = issue.get("file") or issue.get("path")
            extra = f" (file: {file})" if file else ""
            marker = warn_icon if sev == 'WARNING' else (fail_icon if sev == 'ERROR' else ("•" if use_unicode else "*"))
            print(f"- {marker} {sev}: {desc}{extra}")
        print()


def print_report(results: Dict[str, Any]) -> None:
    s = results["summary"]
    print("# StreamlineVPN Project Validation Report\n")
    print("Summary:")
    print(f"- Checks: {s['total_checks']}")
    print(f"- Passed: {s['passed']}")
    print(f"- Failed: {s['failed']}")
    print(f"- Warnings: {s['warnings']}")
    print(f"- Overall: {s['status']}")
    print()
    for name, data in results["checks"].items():
        icon = "✅" if data["status"] == "passed" else "❌"
        print(f"## {icon} {name}")
        issues = data.get("issues", [])
        if not issues:
            print("- No issues found\n")
            continue
        for issue in issues:
            sev = issue.get("severity", "info").upper()
            desc = issue.get("description", "")
            file = issue.get("file") or issue.get("path")
            extra = f" (file: {file})" if file else ""
            print(f"- {sev}: {desc}{extra}")
        print()


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Comprehensive StreamlineVPN Project Validator")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output", help="Write JSON results to file path")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout instead of text report")
    args = parser.parse_args(argv)

    root = Path(args.project_root).resolve()
    results = run_checks(root)

    if args.output:
        Path(args.output).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            # Windows-safe text report with emoji fallback
            print_report_win_safe(results)

    failed = results["summary"].get("failed", 0)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
