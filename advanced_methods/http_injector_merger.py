import argparse
import asyncio
import base64
import io
import json
import zipfile
from pathlib import Path
from typing import List, Tuple, Optional

import aiohttp
from aiohttp import ClientSession

# These advanced merger scripts are intentionally standalone and do not rely
# on the main ``vpn_merger`` configuration.  Proxy settings and test timeouts
# are provided via command line arguments instead.


async def fetch_text(session: ClientSession, url: str, proxy: Optional[str]) -> str:
    """Download text from ``url`` using optional HTTP/SOCKS ``proxy``."""
    async with session.get(url, timeout=30, proxy=proxy) as resp:
        resp.raise_for_status()
        return await resp.text()


def parse_ehi(data: bytes) -> List[str]:
    """Extract raw configs from a .ehi file or text."""
    configs: List[str] = []
    # Try zip archive first
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for name in zf.namelist():
                if name.endswith('.json'):
                    cfg = json.loads(zf.read(name).decode('utf-8', 'ignore'))
                    if isinstance(cfg, dict):
                        raw = cfg.get('payload', '')
                        if raw:
                            configs.append(raw.strip())
        if configs:
            return configs
    except zipfile.BadZipFile:
        pass

    # Maybe base64
    b64chars = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    bdata = data.strip()
    if len(bdata) % 4 == 0 and all(chr(c) in b64chars.decode('ascii') for c in bdata):
        try:
            decoded_bytes = base64.b64decode(bdata)
            # If this looks like a ZIP archive, return as a single string blob
            # to avoid misinterpreting binary as text lines.
            if decoded_bytes.startswith(b"PK\x03\x04"):
                return [decoded_bytes.decode('latin1', 'ignore')]
            # Otherwise, treat as UTF-8 text payload with line-delimited configs
            decoded_text = decoded_bytes.decode('utf-8', 'ignore')
            configs.extend([l.strip() for l in decoded_text.splitlines() if l.strip()])
            if configs:
                return configs
        except Exception:
            pass

    text = data.decode('utf-8', 'ignore')
    configs.extend([l.strip() for l in text.splitlines() if l.strip()])
    return configs


async def test_http_injector(
    session: ClientSession,
    payload: str,
    proxy: Optional[str],
    timeout: float,
) -> bool:
    """Simple connectivity test using an existing ``session``."""
    try:
        url = "http://example.com/"
        headers = {"Host": payload}
        async with session.get(url, headers=headers, proxy=proxy, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


async def process_source(
    url: str, proxy: Optional[str], timeout: float
) -> List[Tuple[str, bool]]:
    async with aiohttp.ClientSession() as session:
        text = await fetch_text(session, url, proxy)
        data = text.encode()
        configs = parse_ehi(data)
        results = []
        for cfg in configs:
            ok = await test_http_injector(session, cfg, proxy, timeout)
            results.append((cfg, ok))
        return results


def save_output(results: List[Tuple[str, bool]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / 'http_injector_raw.txt'
    with open(raw_path, 'w', encoding='utf-8') as f:
        for cfg, ok in results:
            if ok:
                f.write(cfg + '\n')


async def main_async(sources: List[str], output_dir: Path, proxy: Optional[str], timeout: float) -> None:
    all_results: List[Tuple[str, bool]] = []
    for src in sources:
        try:
            res = await process_source(src, proxy, timeout)
            all_results.extend(res)
        except Exception as e:
            print(f"Failed to process {src}: {e}")
    save_output(all_results, output_dir)
    print(f"Saved results to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description='HTTP Injector merger')
    parser.add_argument('--sources', nargs='*', default=[], help='Override source URLs')
    parser.add_argument('--output-dir', default='output_http_injector', help='Output directory')
    parser.add_argument('--proxy', default=None, help='Optional HTTP/SOCKS proxy')
    parser.add_argument('--test-timeout', type=float, default=5.0, help='Connection test timeout in seconds')
    args = parser.parse_args()

    if args.sources:
        sources = args.sources
    else:
        sources = []
        src_file = Path('sources.json')
        if src_file.exists():
            data = json.loads(src_file.read_text())
            sources = data.get('http_injector', [])
    asyncio.run(main_async(sources, Path(args.output_dir), args.proxy, args.test_timeout))


if __name__ == '__main__':
    main()
