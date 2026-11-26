"""Shared fixtures."""

import pytest


@pytest.fixture(scope="session")
def _session_cache_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("panini-cache")


@pytest.fixture(autouse=True)
def _private_cache_dir(monkeypatch, _session_cache_dir) -> None:
    """Tests write their derivation cache to a temporary folder, never to .cache/panini."""
    monkeypatch.setenv("PANINI_CACHE_DIR", str(_session_cache_dir))
