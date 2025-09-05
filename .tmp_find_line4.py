from pathlib import Path
p = Path('src/streamline_vpn/__main__.py')
for i, line in enumerate(p.read_text(encoding='utf-8').splitlines(), start=1):
    if 'process_all(output_dir' in line:
        print(f"{p}:{i}")
    if 'cli.main(standalone_mode=False)' in line:
        print(f"{p}:{i}")
