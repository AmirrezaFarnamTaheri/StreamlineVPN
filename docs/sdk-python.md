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

