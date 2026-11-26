"""On-disk cache of computed derivations: one JSON file per root, keyed by an engine fingerprint.

Layout: ``$PANINI_CACHE_DIR`` (default ``.cache/panini``) / ``derivations`` / <fingerprint> /
<root code>.json. The fingerprint hashes every engine source file and data file, so any change to
the rules, the resolver or the root list is a clean miss: a cached trace is only ever served by the
engine that produced it. Folders for other fingerprints are deleted on the first write.

The cache is best effort. An unreadable or corrupt file is a miss, and a failed write is ignored.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
from functools import cache
from pathlib import Path

ENV = "PANINI_CACHE_DIR"
DEFAULT_DIR = Path(".cache/panini")
PACKAGE = Path(__file__).resolve().parent


def cache_dir() -> Path:
    return Path(os.environ.get(ENV) or DEFAULT_DIR)


def fingerprint_of(package: Path) -> str:
    """Hash of the files a derivation depends on: every .py file of the package outside ``site/``
    (which only renders) and every file under ``data/``. Byte caches are left out."""
    h = hashlib.sha256()
    for path in sorted(package.rglob("*")):
        rel = path.relative_to(package)
        if not path.is_file() or "__pycache__" in rel.parts:
            continue
        if rel.parts[0] == "data" or (path.suffix == ".py" and rel.parts[0] != "site"):
            h.update(rel.as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return h.hexdigest()[:16]


@cache
def fingerprint() -> str:
    """The running engine's fingerprint (computed once per process)."""
    return fingerprint_of(PACKAGE)


class DerivationCache:
    """Per-root derivation JSON on disk. ``root`` defaults to ``cache_dir()``, read on each use."""

    def __init__(self, root: Path | None = None, *, enabled: bool = True):
        self._root = root
        self.enabled = enabled
        self._pruned: set[Path] = set()
        self._lock = threading.Lock()

    @property
    def root(self) -> Path:
        return self._root if self._root is not None else cache_dir()

    def _dir(self) -> Path:
        return self.root / "derivations" / fingerprint()

    def get(self, code: str) -> dict | None:
        if not self.enabled:
            return None
        try:
            data = json.loads(
                (self._dir() / f"{code}.json").read_text(encoding="utf-8")
            )
        except OSError, ValueError:
            return None
        return data if isinstance(data, dict) else None

    def put(self, code: str, data: dict) -> None:
        if not self.enabled:
            return
        here = self._dir()
        try:
            self._prune(here)
            here.mkdir(parents=True, exist_ok=True)
            # Write then rename, so a reader on another server thread never sees half a file.
            tmp = here / f".{code}.{os.getpid()}.{threading.get_ident()}.tmp"
            tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            Path(tmp).replace(here / f"{code}.json")
        except OSError:
            pass

    def _prune(self, keep: Path) -> None:
        """Delete the folders of other fingerprints, once per folder kept."""
        with self._lock:
            if keep in self._pruned:
                return
            self._pruned.add(keep)
        parent = keep.parent
        if parent.is_dir():
            for old in parent.iterdir():
                if old.is_dir() and old.name != keep.name:
                    shutil.rmtree(old, ignore_errors=True)
