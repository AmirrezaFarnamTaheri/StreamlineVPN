import asyncio
from datetime import datetime
from typing import Dict, Any
from pathlib import Path


class HealthChecker:
    def __init__(self, merger_instance):
        self.merger = merger_instance
        self.health_status = {
            'status': 'unknown',
            'last_check': None,
            'components': {}
        }

    async def perform_health_check(self) -> Dict[str, Any]:
        results = {}
        overall = True
        for name, fn in [
            ('database', self._check_database),
            ('disk_space', self._check_disk_space),
        ]:
            try:
                res = await fn()
                results[name] = res
                if not res.get('healthy', False):
                    overall = False
            except Exception as e:
                results[name] = {'healthy': False, 'error': str(e)}
                overall = False
        self.health_status = {
            'status': 'healthy' if overall else 'unhealthy',
            'last_check': datetime.utcnow().isoformat(),
            'components': results,
        }
        return self.health_status

    async def _check_database(self) -> Dict[str, Any]:
        try:
            healthy = self.merger.db is not None
            return {'healthy': healthy}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}

    async def _check_disk_space(self) -> Dict[str, Any]:
        try:
            import shutil
            base = Path('.')
            t, u, f = shutil.disk_usage(base)
            free_gb = f / (1024**3)
            healthy = free_gb >= 1.0
            return {'healthy': healthy, 'free_gb': free_gb}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}


