import argparse
import asyncio
import json
import re
from typing import List, Optional
from pathlib import Path
from typing import List, Optional

# Standalone script: accepts its own proxy and timeout options.


def parse_line(line: str) -> str:
    """Validate and normalize a single endpoint line.

    Parameters
    ----------
    line : str
        A string like ``"ssh://user:pass@host:22"``.

    Returns
    -------
    str
        Normalized ``"scheme://[user:pass@]host:port"`` string.

    Raises
    ------
    TypeError
        If ``line`` is not a ``str``.
    ValueError
        If the line does not match the expected format.
    """

    if not isinstance(line, str):
        raise TypeError("line must be a string")

    text = line.strip()

    # Simplified pattern to avoid catastrophic backtracking from nested quantifiers
    pattern = re.compile(
        r"^(?P<scheme>[A-Za-z][A-Za-z0-9+.-]*)://"  # scheme
        r"(?:(?P<user>[^:@\s]+)(?::(?P<pass>[^@\s]*))?@)?"  # optional user:pass@
        r"(?P<host>[^\s:/@]+)"  # host (no spaces or separators)
        r":(?P<port>\d+)$"  # :port
    )

    m = pattern.match(text)
    if not m:
        raise ValueError(f"Malformed line: {line!r}")

    scheme = m.group("scheme").lower()
    user = m.group("user")
    password = m.group("pass")
    host = m.group("host")
    port_str = m.group("port")

    try:
        port = int(port_str)
    except ValueError as exc:
        raise ValueError(f"Invalid port in line: {line!r}") from exc

    if not (0 < port < 65536):
        raise ValueError(f"Invalid port number in line: {line!r}")

    cred = ""
    if user:
        cred = user
        if password is not None:
            cred += f":{password}"
        cred += "@"

    return f"{scheme}://{cred}{host}:{port}"


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
    asyncio.run(main_async(sources, Path(args.output_dir), args.proxy, args.test_timeout))


if __name__ == '__main__':
    main()
