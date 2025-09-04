"""
Plugin management for the enhanced registry.
"""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugin loading and registration."""

    def __init__(self):
        self._plugins: Dict[str, Any] = {}
        self._plugin_metadata: Dict[str, Dict[str, Any]] = {}
        self._plugin_directories: List[Path] = []

    def add_plugin_directory(self, directory: Path) -> None:
        if directory not in self._plugin_directories:
            self._plugin_directories.append(directory)
            logger.debug(f"Added plugin directory: {directory}")

    def load_plugin(self, plugin_path: str) -> Any:
        try:
            plugin_dir = Path(plugin_path).parent
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))

            module_name = Path(plugin_path).stem
            module = importlib.import_module(module_name)

            plugin_instance = None
            if hasattr(module, "Plugin"):
                plugin_class = getattr(module, "Plugin")
                plugin_instance = plugin_class()
            elif hasattr(module, "create_plugin"):
                plugin_instance = getattr(module, "create_plugin")()
            elif hasattr(module, "main"):
                plugin_instance = getattr(module, "main")

            if plugin_instance:
                self._plugins[module_name] = plugin_instance
                self._plugin_metadata[module_name] = {
                    "path": plugin_path,
                    "module": module,
                    "loaded_at": None,
                }
                logger.info(f"Loaded plugin: {module_name}")
                return plugin_instance
            else:
                logger.warning(f"No plugin found in {plugin_path}")
                return None
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_path}: {e}")
            return None

    def load_plugins_from_directory(self, directory: Path) -> List[Any]:
        loaded_plugins = []
        if not directory.exists():
            logger.warning(f"Plugin directory does not exist: {directory}")
            return loaded_plugins
        for plugin_file in directory.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
            plugin = self.load_plugin(str(plugin_file))
            if plugin:
                loaded_plugins.append(plugin)
        logger.info(f"Loaded {len(loaded_plugins)} plugins from {directory}")
        return loaded_plugins

    def get_plugin(self, name: str) -> Optional[Any]:
        return self._plugins.get(name)

    def get_all_plugins(self) -> Dict[str, Any]:
        return self._plugins.copy()

    def unload_plugin(self, name: str) -> bool:
        if name in self._plugins:
            del self._plugins[name]
            if name in self._plugin_metadata:
                del self._plugin_metadata[name]
            logger.info(f"Unloaded plugin: {name}")
            return True
        return False
