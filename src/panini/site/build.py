"""Build the self-contained HTML explorer: every form and derivation baked in, no server."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
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
    roots = [{"key": r.key, "upadesha_iast": r.upadesha_iast, "meaning": r.meaning, "gana": r.gana,
              "class_label": GANA_LABELS.get(r.gana, r.gana), "pada": r.pada}
             for r in ROOTS.values()]
    return {"roots": roots, "derivations": derivations, "sutras": _sutras(), "markers": MARKER_NOTES}


# What each marker in the slice does, keyed "upadeśa|marker" (both IAST). Markers not listed
# get a generic tooltip. Only effects we are confident of are described.
_STRONG = ("p: a strong ending. Endings without p count as ṅ-marked (1.2.4), and before those "
           "full grade is blocked (1.1.5)")
_CARRIER_L = "carrier vowel: only there to make the l pronounceable"
_AUGMENT = "ṭ: the augment goes at the beginning of what it is added to (1.1.46)"
MARKER_NOTES: dict[str, str] = {
    "lãṭ|ṭ": "primary endings: in the ṭ-tenses (present, the two futures, perfect, subjunctive, "
             "imperative) the middle endings end in -e (3.4.79)",
    "lãṭ|ã": _CARRIER_L,
    "lãṅ|ṅ": "secondary endings: the ṅ-tenses (imperfect, aorist, conditional, optative) take the "
             "shorter endings (3.4.99–101) and, in the past tenses, the augment a- (6.4.71)",
    "lãṅ|ã": _CARRIER_L,
    "paṭhã|ã": "carrier vowel: makes the consonant-final root pronounceable",
    "edhã|ã": "low-pitched (anudātta) marker vowel: the root takes only middle endings (1.3.12)",
    "ḍupacãṣ|ã": "falling-pitched (svarita) marker vowel: the root takes both voices, the middle "
                 "when the action benefits the agent (1.3.72)",
    "ḍupacãṣ|ḍ": "ḍu: the root forms nouns in -trima (3.3.88), e.g. paktrima",
    "ḍupacãṣ|u": "ḍu: the root forms nouns in -trima (3.3.88), e.g. paktrima",
    "ḍupacãṣ|ṣ": "ṣ: the root forms feminine action nouns with the suffix aṅ (3.3.104)",
    "gamḷ̃|ḷ̃": "ḷ: in the active, the root takes the thematic (a-) aorist (3.1.55): agamat",
    "ṇīñ|ñ": "ñ: the root takes both voices, the middle when the action benefits the agent (1.3.72)",
    "tip|p": _STRONG, "sip|p": _STRONG, "mip|p": _STRONG,
    "śap|ś": "ś: makes śap a present-system affix (3.4.113)",
    "śap|p": "p: śap does not count as ṅ-marked, so the root takes full grade before it (bhū → bho)",
    "mahiṅ|ṅ": "ṅ: closes the abbreviation tiṅ (tip … mahiṅ), the name for all the personal endings",
    "aṭ|ṭ": _AUGMENT, "āṭ|ṭ": _AUGMENT,
    # rũ is written into the ending's own term by 8.2.66, so it is keyed by the sound alone.
    "*|ũ": "carrier vowel of rũ (8.2.66): only the r remains",
}


# Plain descriptions of the Dhātupāṭha classes, shown instead of their Sanskrit names.
GANA_LABELS = {"bhvādi": "class 1 · thematic, full grade"}


def _sutras() -> dict[str, dict[str, str]]:
    """Text and gloss of every sūtra in the data file (toy test rules excluded), for tooltips."""
    data = tomllib.loads(files("panini.data").joinpath("sutras.toml").read_text(encoding="utf-8"))
    return {k: {"text": v["text"], "gloss": v["gloss"]} for k, v in data.items() if not k.startswith("9.9.")}


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
