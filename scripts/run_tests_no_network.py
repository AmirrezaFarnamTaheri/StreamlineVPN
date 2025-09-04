import os
import sys
import subprocess


def main() -> int:
    env = os.environ.copy()
    env.setdefault("SKIP_NETWORK", "true")
    # Exercise full suite but let SKIP_NETWORK skip marked tests in conftest.
    cmd = [sys.executable, "-m", "pytest", "-q"]
    try:
        return subprocess.call(cmd, env=env)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

