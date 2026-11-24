"""Build the self-contained HTML explorer: every form and derivation baked in, no server."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from importlib.resources import files
from pathlib import Path

from panini.derivation import Derivation, Status
from panini.engine import derive
from panini.lexicon import ROOTS
from panini.request import all_requests, load_reference

DEFAULT_STYLE_DIR = Path.home() / ".local/state/claude/skills/krish-frontend-style"


def site_data() -> dict:
    """All roots and all 252 requests (unavailable ones included) as plain JSON data."""
    reference = load_reference()
    derivations: dict[str, dict] = {}
    for req in all_requests():
        try:
            d = derive(req, reference=reference)
        except Exception as e:  # one broken derivation must not take the page down
            panini, pie = req.describe()
            ref = reference.get(req.key)
            d = Derivation({"key": req.key, "root": req.root.key, "panini": panini, "pie": pie}, Status.ERROR,
                           None, (), tuple(ref) if ref else None, (), f"{type(e).__name__}: {e}")
        derivations[req.key] = d.to_json()
    roots = [{"key": r.key, "upadesha_iast": r.upadesha_iast, "meaning": r.meaning, "gana": r.gana, "pada": r.pada}
             for r in ROOTS.values()]
    return {"roots": roots, "derivations": derivations}


def _font_css(style_dir: Path) -> str:
    script = style_dir / "scripts" / "font_faces.py"
    if not script.exists():
        print(f"warning: fonts not embedded: {script} not found; using fallback font stacks", file=sys.stderr)
        return ""
    try:
        done = subprocess.run(
            ["uv", "run", "--no-project", str(script), "--embed", "--faces", "body,sans,caps,mono"],
            capture_output=True, text=True, check=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as e:
        print(f"warning: fonts not embedded ({e}); using fallback font stacks", file=sys.stderr)
        return ""
    return done.stdout


def _asset(name: str) -> str:
    return files("panini.site").joinpath(name).read_text(encoding="utf-8")


def build_site(out: Path, style_dir: Path | None = None) -> Path:
    if style_dir is None:
        style_dir = Path(os.environ.get("PANINI_STYLE_DIR", DEFAULT_STYLE_DIR))
    data = json.dumps(site_data(), ensure_ascii=False).replace("</", "<\\/")
    html = (_asset("template.html")
            .replace("/*FONTS*/", _font_css(style_dir))
            .replace("/*BASE_CSS*/", _asset("base.css"))
            .replace("/*PAGE_CSS*/", _asset("style.css"))
            .replace("/*DATA*/", data)
            .replace("/*APP_JS*/", _asset("app.js")))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out
