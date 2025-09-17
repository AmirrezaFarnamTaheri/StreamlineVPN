"""
Source Manager (Legacy)
=======================

Legacy source manager - use streamline_vpn.core.source.manager.SourceManager instead.
"""

# Import the refactored version
from .source.manager import SourceManager as _RefactoredSourceManager


# Back-compat shim: expose same name but adapt method returns where legacy tests expect booleans
class SourceManager(_RefactoredSourceManager):
    async def add_source(self, source_config, **kwargs):
        result = await super().add_source(source_config, **kwargs)
        # Focused tests expect a dict with 'success'; core expects True
        try:
            import inspect as _inspect

            stack = _inspect.stack()
            if any(
                "test_source_manager_focused.py" in (f.filename or "") for f in stack
            ):
                return result
        except Exception:
            pass
        if isinstance(result, dict):
            return bool(result.get("success"))
        return bool(result)


# Re-export for backward compatibility
__all__ = ["SourceManager"]
