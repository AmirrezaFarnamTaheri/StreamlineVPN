"""Mass Config Aggregator Tool - Command Line Interface.

This module provides the command line interface for the aggregator tool.
The core logic is implemented in other modules like pipeline, source_manager, etc.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import logging
import os
import sys
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

from . import vpn_merger
from .config import Settings, load_config
from .constants import CHANNELS_FILE, CONFIG_FILE, SOURCES_FILE
from .output_writer import upload_files_to_gist, write_upload_links
from .pipeline import run_pipeline
from .telegram_scraper import telegram_bot_mode
from .utils import print_public_source_warning


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.utcnow().date()}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def build_parser(
    parser: argparse.ArgumentParser | None = None,
) -> argparse.ArgumentParser:
    """Return an argument parser configured for the aggregator tool."""
    if parser is None:
        parser = argparse.ArgumentParser(
            description=(
                "Mass VPN Config Aggregator. Telegram credentials are only required "
                "when scraping Telegram or running bot mode"
            )
        )
    parser.add_argument("--bot", action="store_true", help="run in telegram bot mode")
    parser.add_argument("--protocols", help="comma separated protocols to keep")
    parser.add_argument(
        "--include-pattern",
        action="append",
        help="regular expression configs must match (can be repeated)",
    )
    parser.add_argument(
        "--exclude-pattern",
        action="append",
        help="regular expression to skip configs (can be repeated)",
    )
    parser.add_argument(
        "--config", default=str(CONFIG_FILE), help="path to config.yaml"
    )
    parser.add_argument(
        "--sources", default=str(SOURCES_FILE), help="path to sources.txt"
    )
    parser.add_argument(
        "--channels", default=str(CHANNELS_FILE), help="path to channels.txt"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="how many hours of Telegram history to scan (default %(default)s)",
    )
    parser.add_argument("--output-dir", help="override output directory from config")
    parser.add_argument(
        "--concurrent-limit",
        type=int,
        help="maximum simultaneous HTTP requests",
    )
    parser.add_argument(
        "--request-timeout",
        type=int,
        help="HTTP request timeout in seconds",
    )
    parser.add_argument(
        "--failure-threshold",
        type=int,
        default=3,
        help="consecutive failures before pruning a source",
    )
    parser.add_argument(
        "--no-prune", action="store_true", help="do not remove failing sources"
    )
    parser.add_argument(
        "--no-base64", action="store_true", help="skip vpn_subscription_base64.txt"
    )
    parser.add_argument(
        "--no-singbox", action="store_true", help="skip vpn_singbox.json"
    )
    parser.add_argument("--no-clash", action="store_true", help="skip clash.yaml")
    parser.add_argument(
        "--write-html",
        action="store_true",
        help="enable vpn_report.html when used with --with-merger",
    )
    parser.add_argument(
        "--shuffle-sources",
        action="store_true",
        help="process sources in random order",
    )
    parser.add_argument(
        "--output-surge",
        metavar="FILE",
        type=str,
        default=None,
        help="write Surge formatted proxy list to FILE",
    )
    parser.add_argument(
        "--output-qx",
        metavar="FILE",
        type=str,
        default=None,
        help="write Quantumult X formatted proxy list to FILE",
    )
    parser.add_argument(
        "--output-xyz",
        metavar="FILE",
        type=str,
        default=None,
        help="write XYZ formatted proxy list to FILE",
    )
    parser.add_argument(
        "--with-merger",
        action="store_true",
        help="run vpn_merger on the aggregated results using the resume feature",
    )
    parser.add_argument(
        "--upload-gist",
        action="store_true",
        help="upload generated files to a GitHub Gist",
    )

    return parser


def main(args: argparse.Namespace | None = None) -> None:
    print_public_source_warning()
    if args is None:
        args = build_parser().parse_args()

    try:
        cfg = load_config(Path(args.config))
    except ValueError:
        print("Config file not found. Copy config.yaml.example to config.yaml.")
        sys.exit(1)

    # Override config with CLI arguments
    if args.output_dir:
        cfg.output_dir = args.output_dir
    if args.concurrent_limit is not None:
        cfg.concurrent_limit = args.concurrent_limit
    if args.request_timeout is not None:
        cfg.request_timeout = args.request_timeout
    if args.no_base64:
        cfg.write_base64 = False
    if args.no_singbox:
        cfg.write_singbox = False
    if args.no_clash:
        cfg.write_clash = False
    if args.write_html:
        cfg.write_html = True
    if args.output_surge is not None:
        cfg.surge_file = args.output_surge
    if args.output_qx is not None:
        cfg.qx_file = args.output_qx
    if args.output_xyz is not None:
        cfg.xyz_file = args.output_xyz
    if args.include_pattern:
        cfg.include_patterns.extend(args.include_pattern)
    if args.exclude_pattern:
        cfg.exclude_patterns.extend(args.exclude_pattern)
    cfg.shuffle_sources = getattr(args, "shuffle_sources", False)

    # Resolve and create directories
    resolved_output = Path(cfg.output_dir).expanduser().resolve()
    resolved_output.mkdir(parents=True, exist_ok=True)
    cfg.output_dir = str(resolved_output)

    resolved_log_dir = Path(cfg.log_dir).expanduser().resolve()
    resolved_log_dir.mkdir(parents=True, exist_ok=True)
    cfg.log_dir = str(resolved_log_dir)

    # Setup logging
    setup_logging(Path(cfg.log_dir))

    protocols = [p.strip().lower() for p in args.protocols.split(",")] if args.protocols else None

    if args.bot:
        # Pass the run_pipeline function to the bot mode to avoid circular imports
        asyncio.run(
            telegram_bot_mode(
                cfg,
                Path(args.sources),
                Path(args.channels),
                args.hours,
                run_pipeline,
            )
        )
    else:
        out_dir, files = asyncio.run(
            run_pipeline(
                cfg,
                Path(args.sources),
                Path(args.channels),
                protocols,
                args.hours,
                failure_threshold=args.failure_threshold,
                prune=not args.no_prune,
            )
        )
        print(f"Aggregation complete. Files written to {out_dir.resolve()}")

        if args.upload_gist:
            token = cfg.github_token or os.environ.get("GITHUB_TOKEN")
            if not token:
                print(
                    "GitHub token not provided. Set github_token in config or GITHUB_TOKEN env var"
                )
            else:
                links = asyncio.run(upload_files_to_gist(files, token))
                path = write_upload_links(links, out_dir)
                print(f"Uploaded files. Links saved to {path}")

        if args.with_merger:
            vpn_merger.CONFIG.resume_file = str(out_dir / "vpn_subscription_raw.txt")
            # Propagate key settings from the aggregator config to the merger
            vpn_merger.CONFIG.output_dir = cfg.output_dir
            vpn_merger.CONFIG.write_base64 = cfg.write_base64
            vpn_merger.CONFIG.write_html = cfg.write_html
            vpn_merger.CONFIG.include_protocols = cfg.include_protocols
            vpn_merger.CONFIG.exclude_protocols = cfg.exclude_protocols
            vpn_merger.CONFIG.exclude_patterns = list(cfg.exclude_patterns)
            vpn_merger.CONFIG.concurrent_limit = cfg.concurrent_limit

            buf = io.StringIO()
            with redirect_stdout(buf):
                vpn_merger.detect_and_run()
            print("\n===== VPN Merger Summary =====")
            print(buf.getvalue().strip())


if __name__ == "__main__":
    main()
