from __future__ import annotations

from pathlib import Path
import sys


def run_merge(args) -> int:
    # Use the new core Merger facade (delegates to legacy run internally)
    from ..core.merger import Merger
    import asyncio
    m = Merger()
    try:
        from .. import vpn_merger as _root  # type: ignore
        _root.CONFIG.output_dir = str(args.output_dir)
    except Exception:
        pass
    # Respect CLI limits if provided
    try:
        if int(args.limit) > 0:
            m.sources = m.sources[: int(args.limit)]
    except Exception:
        pass
    formats = set([f.lower() for f in (args.formats or [])]) if args.formats else None
    asyncio.run(m.run(formats=formats))
    return 0


def run_discover(args) -> int:
    from ..sources.discovery import discover_all
    import asyncio

    urls = asyncio.run(discover_all(limit=args.limit))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("\n".join(urls), encoding="utf-8")
    else:
        sys.stdout.write("\n".join(urls) + "\n")
    return 0


def run_validate(args) -> int:
    from ..core.merger import Merger
    m = Merger()
    urls: list[str] = []
    if args.file:
        try:
            urls = [l.strip() for l in args.file.read_text(encoding="utf-8").splitlines() if l.strip()]
        except Exception as e:
            print(f"Failed to read file: {e}")
            return 2
    else:
        urls = [u.strip() for u in args.urls if u.strip()]
    if not urls:
        print("No URLs provided")
        return 2
    import asyncio
    res = asyncio.run(m.validate_sources(urls, min_score=float(args.min_score)))
    for u, s in res:
        print(f"{s:.2f}\t{u}")
    return 0


def run_format(args) -> int:
    if args.input:
        try:
            text = args.input.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Failed to read input: {e}")
            return 2
    else:
        text = sys.stdin.read()
    lines = [l.rstrip("\n") for l in text.splitlines() if l.strip()]

    if args.type == "base64":
        from ..output.formatters.base64 import to_base64
        out = to_base64(lines)
    elif args.type == "clash":
        from ..output.formatters.clash import to_clash_yaml
        out = to_clash_yaml(lines)
    elif args.type == "singbox":
        from ..output.formatters.singbox import to_singbox_json
        out = to_singbox_json(lines)
    else:
        from ..output.formatters.csv import to_csv
        out = to_csv(lines)

    if args.output:
        from ..output.writer import atomic_write
        atomic_write(args.output, out)
    else:
        sys.stdout.write(out)
        if not out.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def _read_input_lines(path: Path | None) -> list[str]:
    if path:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Failed to read input: {e}")
            return []
    else:
        text = sys.stdin.read()
    return [l.rstrip("\n") for l in text.splitlines() if l.strip()]


def run_filter(args) -> int:
    lines = _read_input_lines(args.input)
    include = set([p.lower() for p in (args.include or [])]) if args.include else None
    exclude = set([p.lower() for p in (args.exclude or [])]) if args.exclude else set()
    out: list[str] = []
    for l in lines:
        proto = l.split("://", 1)[0].lower()
        if include is not None and proto not in include:
            continue
        if proto in exclude:
            continue
        out.append(l)
    data = "\n".join(out)
    if args.output:
        from ..output.writer import atomic_write
        atomic_write(args.output, data)
    else:
        sys.stdout.write(data + ("\n" if not data.endswith("\n") else ""))
    return 0


def run_score(args) -> int:
    lines = _read_input_lines(args.input)
    try:
        from ..core.merger import Merger
        m = Merger()
        sorted_lines = m.score_and_sort(lines)
    except Exception:
        sorted_lines = lines
    top = int(args.top or 0)
    if top > 0:
        sorted_lines = sorted_lines[:top]
    data = "\n".join(sorted_lines)
    if args.output:
        from ..output.writer import atomic_write
        atomic_write(args.output, data)
    else:
        sys.stdout.write(data + ("\n" if not data.endswith("\n") else ""))
    return 0


def run_export(args) -> int:
    lines = _read_input_lines(args.input)
    outdir = args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)
    fmts = set([f.lower() for f in args.formats])
    from ..output.writer import atomic_write
    if "raw" in fmts:
        atomic_write(outdir / "vpn_subscription_raw.txt", "\n".join(lines))
    if "base64" in fmts:
        from ..output.formatters.base64 import to_base64
        atomic_write(outdir / "vpn_subscription_base64.txt", to_base64(lines))
    if "csv" in fmts:
        # Use simple CSV for export convenience
        from ..output.formatters.csv import to_csv
        atomic_write(outdir / "vpn_detailed.csv", to_csv(lines))
    if "singbox" in fmts:
        from ..output.formatters.singbox import to_singbox_json
        atomic_write(outdir / "vpn_singbox.json", to_singbox_json(lines))
    if "clash" in fmts:
        from ..output.formatters.clash import to_clash_yaml
        atomic_write(outdir / "clash.yaml", to_clash_yaml(lines))
    return 0
