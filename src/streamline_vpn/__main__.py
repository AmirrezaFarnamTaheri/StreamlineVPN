"""
StreamlineVPN Command Line Interface
===================================

Main entry point for the StreamlineVPN application.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List

import argparse

from .core.merger import StreamlineVPNMerger
from .utils.logging import setup_logging

logger = logging.getLogger(__name__)


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="StreamlineVPN runner")
    parser.add_argument("--config", type=str, default="config/sources.yaml", help="Path to sources config")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        default=None,
        help="Output format(s). Can be repeated (e.g., --format json --format clash)",
    )
    # Minimal fetcher-related runtime overrides via env-vars
    parser.add_argument("--max-concurrent", type=int, help="Fetcher max concurrent requests")
    parser.add_argument("--timeout", type=int, help="Fetcher timeout seconds")
    parser.add_argument("--retry-attempts", type=int, help="Fetcher retry attempts")
    parser.add_argument("--retry-delay", type=float, help="Fetcher retry delay seconds")

    # Security/env list overrides (comma-separated)
    parser.add_argument("--suspicious-tlds", type=str, help="CSV: suspicious TLDs (e.g., .tk,.ml)")
    parser.add_argument("--safe-protocols", type=str, help="CSV: safe protocols")
    parser.add_argument("--safe-encryptions", type=str, help="CSV: safe encryptions")
    parser.add_argument("--safe-ports", type=str, help="CSV: safe ports (ints)")
    parser.add_argument("--suspicious-patterns", type=str, help="CSV: suspicious text patterns")
    parser.add_argument(
        "--supported-protocol-prefixes",
        type=str,
        help="CSV: supported protocol prefixes (e.g., vmess://,vless://)",
    )

    # Circuit breaker and rate limiter policy overrides
    parser.add_argument("--cb-failure-threshold", type=int, help="Circuit breaker failure threshold")
    parser.add_argument("--cb-recovery-timeout", type=int, help="Circuit breaker recovery timeout seconds")
    parser.add_argument("--rl-max-requests", type=int, help="Rate limiter max requests per window")
    parser.add_argument("--rl-time-window", type=int, help="Rate limiter window seconds")
    parser.add_argument("--rl-burst-limit", type=int, help="Rate limiter burst limit")
    return parser.parse_args(argv)


async def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for StreamlineVPN.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Setup logging
        setup_logging()
        
        args = _parse_args(argv)

        # Apply minimal runtime overrides via environment for settings-aware modules
        if args.max_concurrent is not None:
            os.environ["STREAMLINE_FETCHER_MAX_CONCURRENT"] = str(args.max_concurrent)
        if args.timeout is not None:
            os.environ["STREAMLINE_FETCHER_TIMEOUT_SECONDS"] = str(args.timeout)
        if args.retry_attempts is not None:
            os.environ["STREAMLINE_FETCHER_RETRY_ATTEMPTS"] = str(args.retry_attempts)
        if args.retry_delay is not None:
            os.environ["STREAMLINE_FETCHER_RETRY_DELAY"] = str(args.retry_delay)

        # Security/env overrides via environment variables
        if args.suspicious_tlds:
            os.environ["STREAMLINE_SECURITY_SUSPICIOUS_TLDS"] = args.suspicious_tlds
        if args.safe_protocols:
            os.environ["STREAMLINE_SECURITY_SAFE_PROTOCOLS"] = args.safe_protocols
        if args.safe_encryptions:
            os.environ["STREAMLINE_SECURITY_SAFE_ENCRYPTIONS"] = args.safe_encryptions
        if args.safe_ports:
            os.environ["STREAMLINE_SECURITY_SAFE_PORTS"] = args.safe_ports
        if args.suspicious_patterns:
            os.environ["STREAMLINE_SECURITY_SUSPICIOUS_TEXT_PATTERNS"] = args.suspicious_patterns
        if args.supported_protocol_prefixes:
            os.environ["STREAMLINE_SUPPORTED_PROTOCOL_PREFIXES"] = args.supported_protocol_prefixes

        # Circuit breaker / rate limiter env overrides
        if args.cb_failure_threshold is not None:
            os.environ["STREAMLINE_FETCHER_CB_FAILURE_THRESHOLD"] = str(args.cb_failure_threshold)
        if args.cb_recovery_timeout is not None:
            os.environ["STREAMLINE_FETCHER_CB_RECOVERY_TIMEOUT_SECONDS"] = str(args.cb_recovery_timeout)
        if args.rl_max_requests is not None:
            os.environ["STREAMLINE_FETCHER_RL_MAX_REQUESTS"] = str(args.rl_max_requests)
        if args.rl_time_window is not None:
            os.environ["STREAMLINE_FETCHER_RL_TIME_WINDOW_SECONDS"] = str(args.rl_time_window)
        if args.rl_burst_limit is not None:
            os.environ["STREAMLINE_FETCHER_RL_BURST_LIMIT"] = str(args.rl_burst_limit)

        # Create merger instance
        merger = StreamlineVPNMerger(config_path=args.config)
        
        # Process configurations
        logger.info("Starting StreamlineVPN processing...")
        results = await merger.process_all()
        
        # Save results
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)
        await merger.save_results(str(output_dir), args.formats)
        
        logger.info(f"Processing completed successfully. Results saved to {output_dir}")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return 1


def cli_main() -> int:
    """CLI entry point that handles async execution."""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(cli_main())
