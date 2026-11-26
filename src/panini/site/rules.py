"""Render the same rule catalogue for the static build and the local server."""

from __future__ import annotations

import re
from html import escape
from importlib.resources import files
from string import Template
from typing import Any
from urllib.parse import quote, urlsplit

RULES_DIR = "rules"
INDEX_PAGE = "index.html"
_INLINE = re.compile(
    r"\{([^{}|]+)\|([^{}]+)\}|\[@([a-zA-Z0-9_-]+)\]|\b\d+\.\d+\.\d+(?:\.\d+)?\b"
)
_IAST = re.compile(r"\[\[([^\[\]]+)\]\]")
_KIND = {"definition": "Definition", "operation": "Operation"}


def rule_links(catalog: dict[str, Any]) -> dict[str, str]:
    return {rid: f"{RULES_DIR}/{rid}.html" for rid in catalog["rules"]}


def _link(href: str, text: str, css_class: str = "") -> str:
    css = f' class="{escape(css_class)}"' if css_class else ""
    return f'<a{css} href="{escape(href)}">{escape(text)}</a>'


def _iast(text: str) -> str:
    return f'<span lang="sa-Latn">{escape(text)}</span>'


def _inline_iast(text: str) -> str:
    return "".join(_iast(part) if i % 2 else escape(part) for i, part in enumerate(_IAST.split(text)))


def _term(label_html: str, tip: str, kind: str) -> str:
    return (
        f'<span class="term" tabindex="0" data-tip-kind="{kind}" data-tip="{escape(tip)}">'
        f"{label_html}</span>"
    )


def _sutra_citation(
    rule_id: str, articles: set[str], sutras: dict[str, Any], *, show_text: bool = False
) -> str:
    sutra = sutras.get(rule_id)
    if sutra is None:
        return escape(rule_id)
    heading = f"{rule_id} {sutra['text']}"
    gloss = _INLINE.sub(lambda match: match[1] or match[0], sutra["gloss"])
    gloss = _IAST.sub(r"\1", gloss)
    tip = f"{heading}\n{gloss}"
    label = f"{escape(rule_id)} {_iast(sutra['text'])}" if show_text else escape(rule_id)
    if rule_id in articles:
        return f'<a href="{escape(rule_id)}.html" data-tip-kind="sutra" data-tip="{escape(tip)}">{label}</a>'
    return _term(label, tip, "sutra")


def _reading(
    text: str,
    articles: set[str],
    sutras: dict[str, Any],
    citations: dict[str, tuple[int, str]] | None = None,
) -> str:
    """Render glossary terms, sūtra citations, and references to article sources."""
    parts = []
    start = 0
    for match in _INLINE.finditer(text):
        parts.append(_inline_iast(text[start : match.start()]))
        if match[1]:
            parts.append(_term(_inline_iast(match[1]), match[2], "iast"))
        elif match[3]:
            if citations is None or match[3] not in citations:
                raise ValueError(
                    f"Source {match[3]!r} is missing from the article's citations"
                )
            number, label = citations[match[3]]
            parts.append(f"({_link(f'#source-{number}', label)})")
        else:
            parts.append(_sutra_citation(match[0], articles, sutras))
        start = match.end()
    parts.append(_inline_iast(text[start:]))
    return "".join(parts)


def _rule_reference(
    rule_id: str, note: str, articles: set[str], sutras: dict[str, Any]
) -> str:
    title = _sutra_citation(rule_id, articles, sutras, show_text=True)
    return (
        f"<li>{title}"
        f'<p class="rule-reference-note">{_reading(note, articles, sutras)}</p></li>'
    )


def _refs(title: str, entries: list[str]) -> str:
    if not entries:
        return ""
    return f'<section><h2>{title}</h2><ul class="rule-references">{"".join(entries)}</ul></section>'


def _examples(
    examples: list[dict[str, Any]],
    articles: set[str],
    sutras: dict[str, Any],
    explorer: str,
    available_roots: set[str],
) -> str:
    entries = []
    for example in examples:
        request = example["request"]
        key = request["key"].split("|")
        step = example["step"]
        before = " + ".join(term["iast"] for term in step["before"] if term["iast"])
        after = " + ".join(term["iast"] for term in step["after"] if term["iast"])
        number = example["step_number"]
        step_rule = _sutra_citation(example["step_rule"], articles, sutras)
        trace = ""
        if key[0] in available_roots:
            fragment = "/".join(quote(part, safe="") for part in [*key, str(number)])
            trace = f"<p>{_link(f'{explorer}#{fragment}', 'View this step in the verb trace', 'trace-link')}</p>"
        entries.append(
            f'<article class="rule-example card"><h3>{_iast(example["result"])}</h3>'
            f'<p class="rule-request">{_iast(request["root"])} · {escape(request["pie"])}</p>'
            f'<p class="rule-change">{_iast(before)}'
            f'<span class="arrow" aria-label="becomes">→</span>{_iast(after)}</p>'
            f'<p class="rule-step">Step {number} · {step_rule}</p>'
            f"<p>{_reading(example['note'], articles, sutras)}</p>{trace}</article>"
        )
    return (
        f"<section><h2>Worked examples</h2>{''.join(entries)}</section>"
        if entries
        else ""
    )


def _sources(citations: list[dict[str, str]], sources: dict[str, Any]) -> str:
    entries = []
    for number, citation in enumerate(citations, start=1):
        source = sources[citation["source"]]
        url = source.get("url", "")
        title = source["title"]
        label = (
            _link(url, title)
            if urlsplit(url).scheme in {"https", "http"}
            else escape(title)
        )
        entries.append(
            f'<li id="source-{number}">{label} · {escape(citation["locator"])}</li>'
        )
    return _refs("Sources", entries)


def _article(
    rule: dict[str, Any],
    catalog: dict[str, Any],
    sutras: dict[str, Any],
    explorer: str,
    available_roots: set[str],
) -> str:
    rule_id = rule["id"]
    articles = set(catalog["rules"]) - {rule_id}
    engine = rule["engine"]
    kind = _KIND.get(rule["kind"], rule["kind"].capitalize())
    citations = {
        citation["source"]: (number, citation.get("label", citation["locator"]))
        for number, citation in enumerate(rule["citations"], start=1)
    }
    paragraphs = "".join(
        f"<p>{_reading(paragraph, articles, sutras, citations)}</p>"
        for paragraph in rule["explanation"].strip().split("\n\n")
    )
    scope = (
        f'<p class="rule-scope"><strong>In the explorer.</strong> {_reading(engine["scope"], articles, sutras)}</p>'
        if engine["scope"]
        else ""
    )
    readings = [
        _rule_reference(item["id"], item["note"], articles, sutras)
        for item in engine["readings"]
    ]
    related = dict(rule["related"])
    for rid in engine["blocks"]:
        related.setdefault(
            rid, "This rule can prevent it from applying in the explorer."
        )
    for rid in engine["blocked_by"]:
        related.setdefault(rid, "Can prevent this rule from applying in the explorer.")
    return (
        f'<header><p class="rule-meta">{escape(rule_id)} · {escape(kind)}</p>'
        f"<h1>{_iast(rule['text'])}</h1>"
        f'<p class="rule-gloss">{_reading(rule["gloss"], articles, sutras)}</p></header>'
        f'<section class="rule-explanation"><h2>How to read it</h2>{paragraphs}{scope}</section>'
        + _examples(rule["examples"], articles, sutras, explorer, available_roots)
        + _refs("Rules used in this reading", readings)
        + _refs(
            "Related rules",
            [
                _rule_reference(rid, note, articles, sutras)
                for rid, note in related.items()
            ],
        )
        + _sources(rule["citations"], catalog["sources"])
    )


def render_rule_pages(
    catalog: dict[str, Any],
    sutras: dict[str, Any],
    explorer: str,
    available_roots: set[str],
) -> dict[str, str]:
    """Return a catalogue index and one standalone HTML document per article."""
    template = Template(
        files("panini.site").joinpath("rule_template.html").read_text(encoding="utf-8")
    )
    articles = catalog["rules"]
    rows = "".join(
        f'<li><span class="rule-number">{escape(rid)}</span>'
        f'<span class="rule-name">{_iast(rule["text"])}</span>'
        f'<p class="rule-gloss">{_reading(rule["gloss"], set(), sutras)}</p>'
        f'<a class="rule-open" href="{escape(rid)}.html" '
        f'aria-label="Open {escape(rid)} {escape(rule["text"])}">'
        '<span class="chevron" aria-hidden="true"></span></a></li>'
        for rid, rule in articles.items()
    )
    index = f'<h1>Rules</h1><ul class="rule-index">{rows}</ul>'
    pages = {
        INDEX_PAGE: template.substitute(
            title="Rules",
            verbs=escape(explorer),
            rules_nav='<a href="index.html" aria-current="page">Rules</a>',
            content=index,
        )
    }
    for rid, rule in articles.items():
        pages[f"{rid}.html"] = template.substitute(
            title=escape(f"{rid} {rule['text']}"),
            verbs=escape(explorer),
            rules_nav=_link(INDEX_PAGE, "Rules"),
            content=_article(rule, catalog, sutras, explorer, available_roots),
        )
    return pages
