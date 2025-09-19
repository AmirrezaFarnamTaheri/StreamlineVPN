from __future__ import annotations

import base64
import binascii
import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Set

from .clash_utils import build_clash_config, config_to_clash_proxy
from .config import Settings
from .result_processor import EnhancedConfigProcessor
from .utils import is_valid_config


def output_files(configs: List[str], out_dir: Path, cfg: Settings) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []

    def _atomic_write(path: Path, data: str) -> None:
        tmp = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
        try:
            tmp.write_text(data, encoding="utf-8")
            tmp.replace(path)
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)

    merged_path = out_dir / "vpn_subscription_raw.txt"
    text = "\n".join(configs)
    _atomic_write(merged_path, text)
    written.append(merged_path)

    if cfg.write_base64:
        merged_b64 = out_dir / "vpn_subscription_base64.txt"
        b64_content = base64.b64encode(text.encode()).decode()
        _atomic_write(merged_b64, b64_content)
        written.append(merged_b64)

        try:
            base64.b64decode(b64_content).decode()
        except (binascii.Error, UnicodeDecodeError) as exc:
            logging.warning("Base64 validation failed: %s", exc)

    if cfg.write_singbox:
        outbounds = []
        for idx, link in enumerate(configs):
            proto = link.split("://", 1)[0].lower()
            outbounds.append({"type": proto, "tag": f"node-{idx}", "raw": link})
        merged_singbox = out_dir / "vpn_singbox.json"
        _atomic_write(
            merged_singbox,
            json.dumps({"outbounds": outbounds}, indent=2, ensure_ascii=False),
        )
        written.append(merged_singbox)

    proxies: List[Dict[str, Any]] = []
    need_proxies = cfg.write_clash or cfg.surge_file or cfg.qx_file or cfg.xyz_file
    if need_proxies:
        for idx, link in enumerate(configs):
            proxy = config_to_clash_proxy(link, idx)
            if proxy:
                proxies.append(proxy)

    if cfg.write_clash and proxies:
        clash_yaml = build_clash_config(proxies)
        clash_file = out_dir / "clash.yaml"
        _atomic_write(clash_file, clash_yaml)
        written.append(clash_file)

    if cfg.surge_file and proxies:
        from .advanced_converters import generate_surge_conf

        surge_content = generate_surge_conf(proxies)
        surge_path = Path(cfg.surge_file)
        if not surge_path.is_absolute():
            surge_path = out_dir / surge_path
        _atomic_write(surge_path, surge_content)
        written.append(surge_path)

    if cfg.qx_file and proxies:
        from .advanced_converters import generate_qx_conf

        qx_content = generate_qx_conf(proxies)
        qx_path = Path(cfg.qx_file)
        if not qx_path.is_absolute():
            qx_path = out_dir / qx_path
        _atomic_write(qx_path, qx_content)
        written.append(qx_path)

    if cfg.xyz_file and proxies:
        xyz_lines = [
            f"{p.get('name')},{p.get('server')},{p.get('port')}" for p in proxies
        ]
        xyz_path = Path(cfg.xyz_file)
        if not xyz_path.is_absolute():
            xyz_path = out_dir / xyz_path
        _atomic_write(xyz_path, "\n".join(xyz_lines))
        written.append(xyz_path)

    logging.info(
        "Wrote %s%s%s%s%s%s%s",
        merged_path,
        ", vpn_subscription_base64.txt" if cfg.write_base64 else "",
        ", vpn_singbox.json" if cfg.write_singbox else "",
        ", clash.yaml" if cfg.write_clash and proxies else "",
        f", {Path(cfg.surge_file).name}" if cfg.surge_file else "",
        f", {Path(cfg.qx_file).name}" if cfg.qx_file else "",
        f", {Path(cfg.xyz_file).name}" if cfg.xyz_file else "",
    )

    return written


def deduplicate_and_filter(
    config_set: Set[str], cfg: Settings, protocols: List[str] | None = None
) -> List[str]:
    """Apply filters and return sorted configs.

    If ``protocols`` resolves to an empty list after considering ``cfg.protocols``,
    no protocol filtering is applied and all links are accepted (subject to the
    other filters).
    """
    final = []
    # ``protocols`` overrides ``cfg.protocols`` when provided, even if empty
    if protocols is None:
        protocols = cfg.protocols
    if protocols:
        protocols = [p.lower() for p in protocols]
    exclude = [re.compile(p, re.IGNORECASE) for p in cfg.exclude_patterns]
    include = [re.compile(p, re.IGNORECASE) for p in cfg.include_patterns]
    processor = EnhancedConfigProcessor()
    seen: Set[str] = set()
    for link in sorted(c.strip() for c in config_set):
        l_lower = link.lower()
        link_hash = processor.create_semantic_hash(link)
        if link_hash in seen:
            continue
        seen.add(link_hash)
        if protocols and not any(l_lower.startswith(p + "://") for p in protocols):
            continue
        if any(r.search(l_lower) for r in exclude):
            continue
        if include and not any(r.search(l_lower) for r in include):
            continue
        if not is_valid_config(link):
            continue
        final.append(link)
    logging.info("Final configs count: %d", len(final))
    return final
