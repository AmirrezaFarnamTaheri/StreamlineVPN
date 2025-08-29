from __future__ import annotations

import sys

from .cli.parser import build_parser
from .cli.commands import (
    run_merge,
    run_discover,
    run_validate,
    run_format,
    run_filter,
    run_score,
    run_export,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "merge":
        return run_merge(args)
    if args.command == "discover":
        return run_discover(args)
    if args.command == "validate":
        return run_validate(args)
    if args.command == "format":
        return run_format(args)
    if args.command == "filter":
        return run_filter(args)
    if args.command == "score":
        return run_score(args)
    if args.command == "export":
        return run_export(args)
    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
