import sys
from pathlib import Path
import asyncio

print("--- Starting Import Debugger ---")

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
print("[1/3] System path configured.")

try:
    print("[2/3] Attempting to import StreamlineVPNMerger...")
    from streamline_vpn.core.merger import StreamlineVPNMerger
    print("[2/3] Successfully imported StreamlineVPNMerger.")

    print("[3/3] Attempting to create a StreamlineVPNMerger instance...")
    # We need a dummy session object for instantiation
    class DummySession:
        pass
    merger = StreamlineVPNMerger(session=DummySession())
    print("[3/3] Successfully created a StreamlineVPNMerger instance.")

    print("\n--- Import and Instantiation Test Succeeded ---")

except Exception as e:
    print(f"\n--- Import and Instantiation Test FAILED ---")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()