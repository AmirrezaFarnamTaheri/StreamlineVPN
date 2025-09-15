# Python SDK

## Installation

Use directly from the repository or integrate into your project.

## Usage

```python
from sdk.python.client import SubMergerClient

# Initialize client
client = SubMergerClient(base_url='http://localhost:8000', api_token=None)

# Health checks
print(client.health_v1())
print(client.health_v2())

# Get subscription data
raw = client.sub_raw()
b64 = client.sub_base64()

# Get nodes with pagination and filters (v2 API)
page = client.nodes_v2(
    limit=100, 
    protocol='vmess', 
    reachable=True, 
    host_re='\.edu$', 
    risk='low', 
    anonymize=True
)
print(page['pageInfo'])
for node in page['items']:
    print(node['protocol'], node.get('host'))
```

## Authentication & Multi-tenancy

- If the server requires authentication, pass `api_token=` parameter or set `API_TOKEN` environment variable
- For multi-tenant deployments, set the tenant header via `tenant=` parameter in the client
# Python Examples

You can call the API directly using `requests` (no SDK required).

## Installation

```bash
pip install requests
```

## Usage

```python
import requests

API = 'http://localhost:8080'

# Health
print(requests.get(f"{API}/health").json())

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

