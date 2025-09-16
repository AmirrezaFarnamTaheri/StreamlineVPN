# Python SDK

At present, use the HTTP API directly from Python. A formal SDK may be added later.

## Installation

```bash
pip install requests
```

## Usage

```python
import requests

API = 'http://localhost:8080'

# Health
print(requests.get(f"{API}/api/health").json())

# Statistics
print(requests.get(f"{API}/api/v1/statistics").json())

# Start pipeline
resp = requests.post(
    f"{API}/api/v1/pipeline/run",
    json={"output_dir": "output", "formats": ["json", "clash", "singbox"]},
)
job = resp.json()
print(job)

# Poll status
status = requests.get(f"{API}/api/v1/pipeline/status/{job['job_id']}").json()
print(status)

# List configurations
configs = requests.get(f"{API}/api/v1/configurations?limit=50").json()
print(configs.get('total'), len(configs.get('configurations', [])))

# Sources
print(requests.get(f"{API}/api/v1/sources").json())
print(
    requests.post(
        f"{API}/api/v1/sources", json={"url": "https://test-server.example/configs.txt"}
    ).json()
)
```

If you deploy the Web UI, set `API_BASE_URL` to match your API host so the frontend points to the right place.

