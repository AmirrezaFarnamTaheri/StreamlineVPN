import argparse
import asyncio
import json
import ssl
from pathlib import Path
from typing import List

import aiohttp

from vpn_merger import CONFIG


async def fetch_list(session: aiohttp.ClientSession, url: str) -> List[str]:
    async with session.get(url, timeout=30, proxy=CONFIG.proxy) as resp:
        resp.raise_for_status()
        text = await resp.text()
        return [l.strip() for l in text.splitlines() if l.strip()]


async def test_domain(domain: str) -> bool:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(domain, 443, ssl=ssl.create_default_context(),
                                     server_hostname=domain),
            timeout=CONFIG.test_timeout,
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False


async def process_source(url: str) -> List[str]:
    async with aiohttp.ClientSession() as session:
        items = await fetch_list(session, url)
    results = []
    for item in items:
        domain = item.split('://')[-1]
        if await test_domain(domain):
            results.append(domain)
    return results


def save_output(domains: List[str], output_dir: Path) -> None:
    output_dir.mkdir(exist_ok=True)
    path = output_dir / 'argo_domains.txt'
    path.write_text('\n'.join(domains), encoding='utf-8')


async def main_async(sources: List[str], output_dir: Path) -> None:
    good: List[str] = []
    for src in sources:
        try:
            res = await process_source(src)
            good.extend(res)
        except Exception as e:
            print(f"Failed to fetch {src}: {e}")
    save_output(good, output_dir)
    print(f"Saved {len(good)} domains to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description='ArgoVPN merger')
    parser.add_argument('--sources', nargs='*', default=[], help='Override sources')
    parser.add_argument('--output-dir', default='output_argo', help='Output directory')
    args = parser.parse_args()

    if args.sources:
        sources = args.sources
    else:
        sources = []
        src_file = Path('sources.json')
        if src_file.exists():
            data = json.loads(src_file.read_text())
            sources = data.get('argo', [])
    asyncio.run(main_async(sources, Path(args.output_dir)))


if __name__ == '__main__':
    main()
