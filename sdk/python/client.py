from __future__ import annotations

import os
import typing as t
import requests


class SubMergerClient:
    def __init__(self, base_url: str = 'http://localhost:8000', api_token: str | None = None, tenant: str | None = None):
        self.base = base_url.rstrip('/')
        self.token = api_token or os.environ.get('API_TOKEN')
        self.tenant = tenant

    def _headers(self) -> dict:
        h = {'accept': 'application/json'}
        if self.token:
            h['x-api-token'] = self.token
        if self.tenant:
            h['x-tenant'] = self.tenant
        return h

    # v1
    def sub_raw(self) -> str:
        r = requests.get(f'{self.base}/api/v1/sub/raw', headers=self._headers(), timeout=30)
        r.raise_for_status(); return r.text

    def sub_base64(self) -> str:
        r = requests.get(f'{self.base}/api/v1/sub/base64', headers=self._headers(), timeout=30)
        r.raise_for_status(); return r.text

    def sub_singbox(self) -> dict:
        r = requests.get(f'{self.base}/api/v1/sub/singbox', headers=self._headers(), timeout=30)
        r.raise_for_status(); return r.json()

    def health_v1(self) -> dict:
        r = requests.get(f'{self.base}/api/v1/health', headers=self._headers(), timeout=10)
        r.raise_for_status(); return r.json()

    # v2
    def health_v2(self) -> dict:
        r = requests.get(f'{self.base}/api/v2/health', headers=self._headers(), timeout=10)
        r.raise_for_status(); return r.json()

    def nodes_v2(self, *, cursor: int = 0, limit: int = 100, protocol: str | None = None, reachable: bool | None = None,
                 host_re: str | None = None, risk: str | None = None, anonymize: bool | None = None) -> dict:
        params: dict[str,t.Any] = {'cursor': cursor, 'limit': limit}
        if protocol: params['protocol'] = protocol
        if reachable is not None: params['reachable'] = 'true' if reachable else 'false'
        if host_re: params['host_re'] = host_re
        if risk: params['risk'] = risk
        if anonymize: params['anonymize'] = 'true'
        r = requests.get(f'{self.base}/api/v2/nodes', headers=self._headers(), params=params, timeout=30)
        r.raise_for_status(); return r.json()

