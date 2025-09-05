from pathlib import Path
p = Path('src/streamline_vpn/web/api.py')
for i, line in enumerate(p.read_text(encoding='utf-8').splitlines(), start=1):
    if 'cache_clear' in line:
        print(f"{p}:{i}")
