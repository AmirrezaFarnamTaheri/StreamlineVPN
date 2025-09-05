from pathlib import Path
p = Path('src/streamline_vpn/settings.py')
for i, line in enumerate(p.read_text(encoding='utf-8').splitlines(), start=1):
    if line.strip().startswith('def reset_settings_cache'):
        print(f"{p}:{i}")
