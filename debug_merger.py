import asyncio
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

async def main():
    print("--- Starting Merger Initialization Test ---")
    try:
        from streamline_vpn.core.merger import StreamlineVPNMerger
        print("[1/4] Imported StreamlineVPNMerger successfully.")

        print("[2/4] Attempting to create a StreamlineVPNMerger instance...")
        merger = StreamlineVPNMerger()
        print("[2/4] Created StreamlineVPNMerger instance successfully.")

        print("[3/4] Attempting to initialize the merger...")
        await merger.initialize()
        print("[3/4] Initialized the merger successfully.")

        print("[4/4] Attempting to shut down the merger...")
        await merger.shutdown()
        print("[4/4] Shut down the merger successfully.")

        print("\n--- Merger Initialization Test Succeeded ---")

    except Exception as e:
        print(f"\n--- Merger Initialization Test FAILED ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())