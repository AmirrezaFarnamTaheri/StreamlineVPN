from pathlib import Path
p = Path('src/streamline_vpn/core/merger.py')
for i, line in enumerate(p.read_text(encoding='utf-8').splitlines(), start=1):
    if 'self.results = enhanced_configs' in line:
        print(f"{p}:{i}")
    if 'exc_info=True' in line and 'process_all' in open(p, 'r', encoding='utf-8').read():
        pass
