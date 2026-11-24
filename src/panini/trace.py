"""Plain-text rendering of a derivation (for the terminal and for debugging)."""

from __future__ import annotations

import re

from panini.derivation import Derivation, Status, StepRecord
from panini.rules.base import sutra_info


_UNCHANGED = {
    "category": "(form unchanged: assigns a category later rules use) ",
    "prohibition": "(form unchanged: prevents another rule) ",
}


_TERM = re.compile(r"\{([^{}|]+)\|([^{}]+)\}")


def plain(text: str, verbosity: int = 0) -> str:
    """Render {modern|traditional} markup: the modern word, plus the traditional one at -v."""
    return _TERM.sub(r"\1 (\2)" if verbosity >= 1 else r"\1", text)


def _form(views) -> str:
    return " + ".join(v.iast() for v in views)


def _text(rule_id: str) -> str:
    try:
        return sutra_info(rule_id)[0]
    except KeyError:
        return ""


def render_text(d: Derivation, verbosity: int = 0) -> str:
    """The prakriyā as numbered steps: form, sūtra, note; '↳' for near-misses.

    verbosity 1 adds the competitors each step beat (✗); verbosity 2 also shows the
    form before each step and any warnings.
    """
    root = d.request.get("root", "?")
    head = f"{root}-, {d.request.get('panini', '')}  →  "
    if d.status is Status.UNAVAILABLE:
        return head + f"(no form: {d.message})"
    if d.status is Status.ERROR:
        return head + f"(error: {plain(d.message or '')})"
    lines = [head + (d.result or ""),
             "    notation: capitals = markers (it), ã = nasal vowel, + = boundary between elements"]
    if d.alternatives:
        lines.append(f"    also correct: {', '.join(d.alternatives)}")
    lines.append("")
    width = max((len(_form(s.after)) for s in d.steps), default=10) + 2
    for n, s in enumerate(d.steps, 1):
        lines.extend(_render_step(n, s, width, verbosity))
    return "\n".join(lines)


def _render_step(n: int, s: StepRecord, width: int, verbosity: int) -> list[str]:
    rid = s.rule_ids[0]
    out = []
    if verbosity >= 2:
        out.append(f"{'':>4}  {'(' + _form(s.before) + ')':<{width}}")
    out.append(f"{n:>4}  {_form(s.after):<{width}}{rid:<9}{_text(rid)}")
    if s.note:
        out.append(f"{'':>4}  {'':<{width}}{'':<9}{_UNCHANGED.get(s.kind, '')}{plain(s.note, verbosity)}")
    for nm in s.near_misses:
        out.append(f"{'':>4}  ↳ {plain(nm, verbosity)}")
    if verbosity >= 1:
        for l in s.losers:
            out.append(f"{'':>4}     ✗ {l.rule_id}: {plain(l.reason, verbosity)}")
    if verbosity >= 2:
        for w in s.warnings:
            out.append(f"{'':>4}     ! {plain(w, verbosity)}")
    return out
