import os
from pathlib import Path

from streamline_vpn.web.api.routes import find_config_path


def test_find_config_path_env_priority(tmp_path, monkeypatch):
    env_file = tmp_path / "env_sources.yaml"
    env_file.write_text("sources: []")
    monkeypatch.setenv("APP_CONFIG_PATH", str(env_file))
    monkeypatch.chdir(tmp_path)
    assert find_config_path() == env_file


def test_find_config_path_cwd(tmp_path, monkeypatch):
    monkeypatch.delenv("APP_CONFIG_PATH", raising=False)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cwd_file = config_dir / "sources.yaml"
    cwd_file.write_text("sources: []")
    monkeypatch.chdir(tmp_path)
    assert find_config_path() == cwd_file


def test_find_config_path_none(tmp_path, monkeypatch):
    monkeypatch.delenv("APP_CONFIG_PATH", raising=False)
    monkeypatch.chdir(tmp_path)
    assert find_config_path() is None
