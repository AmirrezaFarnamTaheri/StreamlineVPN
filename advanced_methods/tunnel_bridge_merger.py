import argparse
import asyncio
import json
from pathlib import Path
from typing import List, Optional

# These scripts also update ``vpn_merger.CONFIG.proxy`` when present.
try:
    from vpn_merger import CONFIG
except Exception:  # pragma: no cover
    CONFIG = None


def parse_line(line: str) -> str:
    return line.strip()


async def test_endpoint(host: str, port: int, timeout: float) -> bool:
    try:
        fut = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(fut, timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False


async def process_source(path: str, timeout: float) -> List[str]:
    endpoints: List[str] = []
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    for line in lines:
        if '://' not in line:
            continue
        parsed = parse_line(line)
        url = parsed.split('://', 1)[1]
        if '@' in url:
            url = url.split('@', 1)[1]
        if ':' in url:
            host, port = url.split(':', 1)
            try:
                port = int(port)
            except ValueError:
                continue
            if await test_endpoint(host, port, timeout):
                endpoints.append(parsed)
    return endpoints


def save_output(endpoints: List[str], output_dir: Path) -> None:
    output_dir.mkdir(exist_ok=True)
    path = output_dir / 'tunnel_endpoints.txt'
    path.write_text('\n'.join(endpoints), encoding='utf-8')


from typing import Optional


async def main_async(sources: List[str], output_dir: Path, proxy: Optional[str], timeout: float) -> None:
    good: List[str] = []
    for src in sources:
        try:
            res = await process_source(src, timeout)
            good.extend(res)
        except Exception as e:
            print(f"Failed to read {src}: {e}")
    save_output(good, output_dir)
    print(f"Saved {len(good)} endpoints to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description='Tunnel/Bridge merger')
    parser.add_argument('--sources', nargs='*', default=[], help='Files containing endpoints')
    parser.add_argument('--output-dir', default='output_tunnel', help='Output directory')
    parser.add_argument('--proxy', default=None, help='Optional HTTP/SOCKS proxy (unused)')
    parser.add_argument('--test-timeout', type=float, default=5.0, help='Connection test timeout in seconds')
    args = parser.parse_args()

    sources = args.sources
    if not sources:
        src_file = Path('sources.json')
        if src_file.exists():
            data = json.loads(src_file.read_text())
            sources = data.get('tunnel_bridge', [])
    if CONFIG is not None:
        CONFIG.proxy = args.proxy
    asyncio.run(main_async(sources, Path(args.output_dir), args.proxy, args.test_timeout))


if __name__ == '__main__':
    main()
