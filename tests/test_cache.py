"""The on-disk derivation cache (panini.cache) and its use by the site."""

import json

import pytest
from panini import cache
from panini.cache import DerivationCache, fingerprint_of
from panini.site import build


@pytest.fixture
def disk(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "fingerprint", lambda: "fp1")
    return DerivationCache(tmp_path)


def test_round_trip_and_miss(disk):
    assert disk.get("01.0001") is None
    disk.put("01.0001", {"k": {"result": "bhavati"}})
    assert disk.get("01.0001") == {"k": {"result": "bhavati"}}
    assert (disk.root / "derivations/fp1/01.0001.json").is_file()
    assert not list((disk.root / "derivations/fp1").glob(".*.tmp"))


def test_corrupt_or_wrong_shape_file_is_a_miss(disk):
    disk.put("01.0001", {"k": 1})
    path = disk.root / "derivations/fp1/01.0001.json"
    path.write_text("{not json", encoding="utf-8")
    assert disk.get("01.0001") is None
    path.write_text("[1, 2]", encoding="utf-8")
    assert disk.get("01.0001") is None


def test_another_fingerprint_misses_and_its_folder_is_pruned(disk, monkeypatch):
    disk.put("01.0001", {"k": 1})
    monkeypatch.setattr(cache, "fingerprint", lambda: "fp2")
    assert disk.get("01.0001") is None
    disk.put("01.0002", {"k": 2})
    assert not (disk.root / "derivations/fp1").exists()
    assert disk.get("01.0002") == {"k": 2}


def test_disabled_cache_neither_reads_nor_writes(disk):
    disk.put("01.0001", {"k": 1})
    disk.enabled = False
    assert disk.get("01.0001") is None
    disk.put("01.0002", {"k": 2})
    assert not (disk.root / "derivations/fp1/01.0002.json").exists()


def test_a_failed_write_is_ignored(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "fingerprint", lambda: "fp1")
    blocker = tmp_path / "file"
    blocker.write_text("not a folder")
    DerivationCache(blocker).put(
        "01.0001", {"k": 1}
    )  # can't mkdir under a file: no exception


def test_default_root_follows_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("PANINI_CACHE_DIR", str(tmp_path))
    assert DerivationCache().root == tmp_path
    monkeypatch.delenv("PANINI_CACHE_DIR")
    assert DerivationCache().root == cache.DEFAULT_DIR


def test_fingerprint_covers_engine_code_and_data_but_not_rendering(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "site").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "engine.py").write_text("a = 1")
    (tmp_path / "data/roots.tsv").write_text("bhU")
    (tmp_path / "site/app.js").write_text("x")
    (tmp_path / "site/build.py").write_text("x")
    base = fingerprint_of(tmp_path)

    (tmp_path / "site/app.js").write_text("y")
    (tmp_path / "site/build.py").write_text("y")
    (tmp_path / "__pycache__/engine.pyc").write_bytes(b"\0")
    assert fingerprint_of(tmp_path) == base

    (tmp_path / "data/roots.tsv").write_text("BU")
    changed_data = fingerprint_of(tmp_path)
    assert changed_data != base
    (tmp_path / "engine.py").write_text("a = 2")
    assert fingerprint_of(tmp_path) not in (base, changed_data)


def test_site_reads_a_cached_root_without_deriving(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "DISK_CACHE", DerivationCache(tmp_path))
    build.root_derivations.cache_clear()
    try:
        first = build.root_derivations("01.0242")
        assert first["01.0242|laṭ|P|3|sg"]["result"] == "yucchati"
        assert (
            json.loads(
                next((tmp_path / "derivations").glob("*/01.0242.json")).read_text()
            )
            == first
        )

        def no_engine(*_args, **_kwargs):
            raise AssertionError("derived although the root was cached")

        monkeypatch.setattr(build, "derive", no_engine)
        build.root_derivations.cache_clear()
        assert build.root_derivations("01.0242") == first
    finally:
        build.root_derivations.cache_clear()


def test_a_root_with_a_crashed_derivation_is_not_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "DISK_CACHE", DerivationCache(tmp_path))
    real = build.derive

    def flaky(req, **kw):
        if req.key == "01.0242|laṭ|P|3|sg":
            raise RuntimeError("boom")
        return real(req, **kw)

    monkeypatch.setattr(build, "derive", flaky)
    build.root_derivations.cache_clear()
    try:
        assert (
            build.root_derivations("01.0242")["01.0242|laṭ|P|3|sg"]["status"] == "error"
        )
        assert not list(tmp_path.rglob("01.0242.json"))
    finally:
        build.root_derivations.cache_clear()
