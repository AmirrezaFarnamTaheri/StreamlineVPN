import argparse
import asyncio
import base64
import io
import json
import zipfile
from pathlib import Path
from typing import List, Tuple

import aiohttp
from aiohttp import ClientSession

from vpn_merger import CONFIG


async def fetch_text(session: ClientSession, url: str) -> str:
    async with session.get(url, timeout=30, proxy=CONFIG.proxy) as resp:
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
            decoded = base64.b64decode(bdata).decode('utf-8', 'ignore')
            configs.extend([l.strip() for l in decoded.splitlines() if l.strip()])
            if configs:
                return configs
        except Exception:
            pass

    text = data.decode('utf-8', 'ignore')
    configs.extend([l.strip() for l in text.splitlines() if l.strip()])
    return configs


async def test_http_injector(payload: str) -> bool:
    """Simple connectivity test using aiohttp."""
    try:
        url = 'http://example.com/'
        headers = {"Host": payload}
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=headers, proxy=CONFIG.proxy, timeout=5) as r:
                return r.status == 200
    except Exception:
        return False


async def process_source(url: str) -> List[Tuple[str, bool]]:
    async with aiohttp.ClientSession() as session:
        text = await fetch_text(session, url)
        data = text.encode()
        configs = parse_ehi(data)
        results = []
        for cfg in configs:
            ok = await test_http_injector(cfg)
            results.append((cfg, ok))
        return results


def save_output(results: List[Tuple[str, bool]], output_dir: Path) -> None:
    output_dir.mkdir(exist_ok=True)
    raw_path = output_dir / 'http_injector_raw.txt'
    with open(raw_path, 'w', encoding='utf-8') as f:
        for cfg, ok in results:
            if ok:
                f.write(cfg + '\n')


async def main_async(sources: List[str], output_dir: Path) -> None:
    all_results: List[Tuple[str, bool]] = []
    for src in sources:
        try:
            res = await process_source(src)
            all_results.extend(res)
        except Exception as e:
            print(f"Failed to process {src}: {e}")
    save_output(all_results, output_dir)
    print(f"Saved results to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description='HTTP Injector merger')
    parser.add_argument('--sources', nargs='*', default=[], help='Override source URLs')
    parser.add_argument('--output-dir', default='output_http_injector', help='Output directory')
    args = parser.parse_args()

    if args.sources:
        sources = args.sources
    else:
        sources = []
        src_file = Path('sources.json')
        if src_file.exists():
            data = json.loads(src_file.read_text())
            sources = data.get('http_injector', [])
    asyncio.run(main_async(sources, Path(args.output_dir)))


if __name__ == '__main__':
    main()
