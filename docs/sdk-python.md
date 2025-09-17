Python SDK
==========

Install
-------

Use directly from the repo or vendor into your project.

Usage
-----

```python
from sdk.python.client import SubMergerClient

client = SubMergerClient(base_url='http://localhost:8000', api_token=None)

print(client.health_v1())
print(client.health_v2())

# Raw/base64
raw = client.sub_raw()
b64 = client.sub_base64()

# Nodes (v2) with pagination and filters
page = client.nodes_v2(limit=100, protocol='vmess', reachable=True, host_re='\.edu$', risk='low', anonymize=True)
print(page['pageInfo'])
for node in page['items']:
    print(node['protocol'], node.get('host'))
```

Auth & Tenancy
--------------

- If the server requires a token, pass `api_token=` or set `API_TOKEN` env.
- For multi-tenant mode, set header via `tenant=` in the client.

