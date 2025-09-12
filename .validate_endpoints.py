import os
os.environ['CACHE_ENABLED']='1'
from fastapi.testclient import TestClient
from streamline_vpn.web.unified_api import create_unified_app

app = create_unified_app()

with TestClient(app) as client:
    checks = []
    r = client.get('/health'); print('health:', r.status_code, r.json().get('merger_initialized'))
    r = client.get('/api/v1/cache/health'); print('cache_health:', r.status_code, r.json().get('cache'))
    r = client.post('/api/v1/cache/clear'); print('cache_clear:', r.status_code, r.json().get('status'))
    r = client.get('/api/v1/statistics'); print('statistics:', r.status_code)
    r = client.post('/api/v1/sources/validate'); print('sources_validate:', r.status_code)
