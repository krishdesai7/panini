"""Site data and the explorer page: baked in whole for the static build, per root for the server."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from collections.abc import Iterable
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from urllib.parse import quote

from panini.cache import DerivationCache
from panini.derivation import Derivation, Status
from panini.engine import derive
from panini.lexicon import FEATURED, ROOTS
from panini.request import OUT_OF_SCOPE, all_requests, effective_pada, load_reference
from panini.rule_catalog import build_catalog
from panini.site.rules import RULES_DIR, render_rule_pages, rule_links

DEFAULT_STYLE_DIR = Path.home() / ".local/state/claude/skills/krish-frontend-style"


def root_entries() -> list[dict]:
    """One entry per root: what the picker and the heading need."""
    return [{"key": r.key, "name": r.name, "upadesha_iast": r.upadesha_iast, "meaning": r.meaning,
             "meaning_kind": r.meaning_kind, "gana": r.gana, "class_label": GANA_LABELS.get(r.gana, r.gana),
             "pada": effective_pada(r), "unavailable": OUT_OF_SCOPE[r.code][0] if r.code in OUT_OF_SCOPE else None,
             "unavailable_rule": OUT_OF_SCOPE[r.code][1] if r.code in OUT_OF_SCOPE else None}
            for r in ROOTS.values()]


DISK_CACHE = DerivationCache()


def use_disk_cache(enabled: bool) -> None:
    """Turn the on-disk derivation cache (panini.cache) on or off for this process."""
    DISK_CACHE.enabled = enabled


@lru_cache(maxsize=128)
def root_derivations(code: str) -> dict[str, dict]:
    """Every request of one root (unavailable ones included): request key -> Derivation.to_json().

    Looked up in memory, then on disk (keyed by the engine's fingerprint), then derived."""
    if (hit := DISK_CACHE.get(code)) is not None:
        return hit
    reference = load_reference()
    out: dict[str, dict] = {}
    crashed = False
    for req in all_requests([code]):
        try:
            d = derive(req, reference=reference)
        except Exception as e:  # one broken derivation must not take the page down
            crashed = True
            panini, pie = req.describe()
            ref = reference.get(req.key)
            d = Derivation({"key": req.key, "root": req.root.name, "panini": panini, "pie": pie}, Status.ERROR,
                           None, (), tuple(ref) if ref else None, (), f"{type(e).__name__}: {e}")
        out[req.key] = d.to_json()
    if not crashed:  # a crash is a bug; once it's fixed the root must be derived again
        DISK_CACHE.put(code, out)
    return out


def site_data(codes: Iterable[str] | None, *, embed_all_roots: bool) -> dict:
    """Page data. Derivations are embedded for `codes` (None: every root); the root list covers
    every root if `embed_all_roots`, else just `codes`."""
    codes = list(ROOTS) if codes is None else list(codes)
    entries = {e["key"]: e for e in root_entries()}
    roots = list(entries.values()) if embed_all_roots else [entries[c] for c in codes]
    derivations = {k: v for code in codes for k, v in root_derivations(code).items()}
    return {"roots": roots, "derivations": derivations, "sutras": _sutras(), "markers": MARKER_NOTES,
            "glossary": GLOSSARY, "featured": list(FEATURED)}


# Names kept in the text but explained on hover wherever they occur as whole words.
GLOSSARY = {"laṭ": "present imperfective", "laṅ": "past imperfective"}


# What each marker in the slice does, keyed "upadeśa|marker" (both IAST). Markers not listed
# get a generic tooltip. Only effects we are confident of are described.
_STRONG = ("p: a strong ending. Endings without p count as ṅ-marked (1.2.4), and before those "
           "full grade is blocked (1.1.5)")
_CARRIER_L = "carrier vowel: only there to make the l pronounceable"
_AUGMENT = "ṭ: the augment goes at the beginning of what it is added to (1.1.46)"
MARKER_NOTES: dict[str, str] = {
    "lãṭ|ṭ": "primary endings: the ṭ-marked lakāras, laṭ (present), liṭ (perfect), luṭ and lṛṭ "
             "(futures), leṭ (Vedic subjunctive) and loṭ (imperative), take middle endings in -e (3.4.79; "
             "the imperative then changes them further)",
    "lãṭ|ã": _CARRIER_L,
    "lãṅ|ṅ": "secondary endings: the ṅ-marked lakāras, laṅ (imperfect), luṅ (aorist), lṛṅ "
             "(conditional) and liṅ (optative), take the shorter endings (3.4.99–101); all but liṅ also "
             "take the augment a- (6.4.71)",
    "lãṅ|ã": _CARRIER_L,
    "paṭhã|ã": "protects the root's final ṭh, which as the last sound taught would itself be a marker "
               "(1.3.3); it also carries the root's pitch, here neither low nor falling, so the root "
               "is active (1.3.78)",
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


def stylesheet(style_dir: Path | None) -> str:
    if style_dir is None:
        style_dir = Path(os.environ.get("PANINI_STYLE_DIR", DEFAULT_STYLE_DIR))
    return "\n".join((_font_css(style_dir), _asset("base.css"), _asset("style.css")))


def rule_assets(catalog: dict, explorer_href: str, roots: set[str], css: str) -> dict[str, str]:
    return {
        **render_rule_pages(catalog, _sutras(), explorer_href, roots),
        "style.css": css + "\n" + _asset("rules.css"),
        "theme.js": _asset("theme.js"),
        "tooltip.js": _asset("tooltip.js"),
    }


def page_html(data: dict, style_dir: Path | None, *, css: str | None = None) -> str:
    """The explorer page with `data` and (if `style_dir` has them) the fonts embedded."""
    if css is None:
        css = stylesheet(style_dir)
    return (_asset("template.html")
            .replace("/*PAGE_CSS*/", css)
            .replace("/*THEME_JS*/", _asset("theme.js"))
            .replace("/*DATA*/", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
            .replace("/*TOOLTIP_JS*/", _asset("tooltip.js"))
            .replace("/*APP_JS*/", _asset("app.js")))


def build_site(out: Path, style_dir: Path | None = None) -> Path:
    """Write the verb explorer and its sibling rule pages for offline browsing."""
    catalog = build_catalog()
    css = stylesheet(style_dir)
    data = {**site_data(FEATURED, embed_all_roots=False), "source": "static",
            "rule_pages": rule_links(catalog)}
    html = page_html(data, style_dir, css=css)
    rule_dir = out.parent / RULES_DIR
    rule_dir.mkdir(parents=True, exist_ok=True)
    explorer_href = f"../{quote(out.name, safe='')}"
    for name, content in rule_assets(catalog, explorer_href, set(FEATURED), css).items():
        (rule_dir / name).write_text(content, encoding="utf-8")
    out.write_text(html, encoding="utf-8")
    return out
