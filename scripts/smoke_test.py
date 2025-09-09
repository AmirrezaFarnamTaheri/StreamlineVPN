import json
import time
from urllib.request import urlopen, Request
import urllib.request


def get(url: str, timeout: float = 5.0, headers: dict | None = None):
    try:
        req = Request(url, headers=headers or {})
        with urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("content-type", ""), r.read()
    except Exception as e:  # noqa: BLE001 - simple smoke test
        return None, None, str(e).encode()


def main() -> int:
    api = "http://127.0.0.1:8080"
    web = "http://127.0.0.1:8000"

    # Wait for API
    api_ok = False
    for _ in range(40):
        s, _, _ = get(f"{api}/health")
        if s == 200:
            api_ok = True
            break
        time.sleep(0.5)
    print("API /health:", api_ok)

    # Web api-base.js
    s, _, _ = get(f"{web}/api-base.js")
    print("WEB /api-base.js:", s)

    # Core API endpoints
    for path in [
        "/api/v1/statistics",
        "/api/v1/configurations?limit=1",
        "/api/v1/sources",
    ]:
        s, ct, content = get(f"{api}{path}")
        note = ""
        if s is None:
            note = f" error: {content[:80]!r}"
        print(f"GET {path} -> {s}{note}")

    # Try versioned pipeline run
    payload = json.dumps(
        {
            "config_path": "config/sources.unified.yaml",
            "output_dir": "output",
            "formats": ["json"],
        }
    ).encode()

    def post(url: str):
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=15,
            )
            body = r.read().decode("utf-8", "ignore")
            return r.status, body
        except Exception as e:  # noqa: BLE001
            return None, str(e)

    status, body = post(f"{api}/api/v1/pipeline/run")
    print("POST /api/v1/pipeline/run ->", status)
    if status != 200:
        status2, body2 = post(f"{api}/pipeline/run")
        print("POST /pipeline/run ->", status2)
        if status2 == 200:
            body = body2
            status = status2

    job_id = None
    try:
        data = json.loads(body)
        job_id = data.get("job_id") if isinstance(data, dict) else None
    except Exception:
        pass

    # Poll job if available
    if job_id:
        # try v1 status first, then legacy /jobs/{id}
        for _ in range(30):
            s, _, content = get(f"{api}/api/v1/pipeline/status/{job_id}")
            if s != 200:
                s2, _, content2 = get(f"{api}/jobs/{job_id}")
                print("status poll v1:", s, " legacy:", s2)
                if s2 == 200:
                    content = content2
                    s = s2
                else:
                    time.sleep(1)
                    continue
            try:
                st = json.loads(content)
            except Exception:
                print("status parse error")
                break
            print("status:", st.get("status"), "progress:", st.get("progress"), "msg:", st.get("message"))
            if st.get("status") in {"completed", "failed"}:
                break
            time.sleep(2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


