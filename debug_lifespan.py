import sys
from pathlib import Path
import asyncio

print("--- Starting Lifespan Debugger ---")

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
print("[1/3] System path configured.")

async def main():
    try:
        print("[2/3] Importing and creating the application...")
        from streamline_vpn.web.unified_api import create_unified_app
        app = create_unified_app()
        print("[2/3] Application created successfully.")

        print("[3/3] Manually running application startup logic...")
        # This simulates the startup part of the lifespan context manager
        async with app.router.lifespan_context(app):
             print("[3/3] Application startup logic completed successfully.")
             # The 'yield' happens here. We don't need to do anything inside the 'with' block.
             pass

        print("\n--- Lifespan Test Succeeded ---")

    except Exception as e:
        print(f"\n--- Lifespan Test FAILED ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # This will raise an exception if the event loop is already running,
    # which is a useful diagnostic in itself.
    asyncio.run(main())