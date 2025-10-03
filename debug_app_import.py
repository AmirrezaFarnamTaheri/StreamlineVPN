import sys
from pathlib import Path
import asyncio

print("--- Starting Application Import Test ---")

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
print("[1/2] System path configured.")

try:
    print("[2/2] Attempting to import the application factory...")
    from streamline_vpn.web.unified_api import create_unified_app
    print("[2/2] Successfully imported the application factory.")

    # We will not call the function, only import it.
    # The goal is to test the import chain.

    print("\n--- Application Import Test Succeeded ---")

except Exception as e:
    print(f"\n--- Application Import Test FAILED ---")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()