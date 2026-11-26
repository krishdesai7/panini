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
_INLINE = re.compile(r"\{([^{}|]+)\|([^{}]+)\}|\b\d+\.\d+\.\d+(?:\.\d+)?\b")
_KIND = {"definition": "Definition", "operation": "Operation"}


def rule_links(catalog: dict[str, Any]) -> dict[str, str]:
    return {rid: f"{RULES_DIR}/{rid}.html" for rid in catalog["rules"]}


def _link(href: str, text: str, css_class: str = "") -> str:
    css = f' class="{escape(css_class)}"' if css_class else ""
    return f'<a{css} href="{escape(href)}">{escape(text)}</a>'


def _reading(text: str, articles: dict[str, Any]) -> str:
    """Render glossary markup and link sūtra numbers that have an article."""
    parts = []
    start = 0
    for match in _INLINE.finditer(text):
        parts.append(escape(text[start : match.start()]))
        if match[1]:
            parts.append(f'<abbr title="{escape(match[2])}">{escape(match[1])}</abbr>')
        elif match[0] in articles:
            parts.append(_link(f"{match[0]}.html", match[0]))
        else:
            parts.append(escape(match[0]))
        start = match.end()
    parts.append(escape(text[start:]))
    return "".join(parts)


def _rule_reference(
    rule_id: str, note: str, articles: dict[str, Any], sutras: dict[str, Any]
) -> str:
    label = f"{rule_id} {sutras[rule_id]['text']}" if rule_id in sutras else rule_id
    title = _link(f"{rule_id}.html", label) if rule_id in articles else escape(label)
    return f"<li>{title} · {_reading(note, articles)}</li>"


def _refs(title: str, entries: list[str]) -> str:
    if not entries:
        return ""
    return f'<section><h2>{title}</h2><ul class="rule-references">{"".join(entries)}</ul></section>'


def _examples(
    examples: list[dict[str, Any]],
    articles: dict[str, Any],
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
        step_rule = _reading(example["step_rule"], articles)
        trace = ""
        if key[0] in available_roots:
            fragment = "/".join(quote(part, safe="") for part in [*key, str(number)])
            trace = f"<p>{_link(f'{explorer}#{fragment}', 'View this step in the verb trace', 'trace-link')}</p>"
        entries.append(
            f'<article class="rule-example card"><h3>{escape(example["result"])}</h3>'
            f'<p class="rule-request">{escape(request["root"])} · {escape(request["pie"])}</p>'
            f'<p class="rule-change"><span>{escape(before)}</span>'
            f'<span class="arrow" aria-label="becomes">→</span><span>{escape(after)}</span></p>'
            f'<p class="rule-step">Step {number} · {step_rule}</p>'
            f"<p>{_reading(example['note'], articles)}</p>{trace}</article>"
        )
    return (
        f"<section><h2>Worked examples</h2>{''.join(entries)}</section>"
        if entries
        else ""
    )


def _sources(citations: list[dict[str, str]], sources: dict[str, Any]) -> str:
    entries = []
    for citation in citations:
        source = sources[citation["source"]]
        url = source.get("url", "")
        title = source["title"]
        label = (
            _link(url, title)
            if urlsplit(url).scheme in {"https", "http"}
            else escape(title)
        )
        entries.append(f"<li>{label} · {escape(citation['locator'])}</li>")
    return _refs("Sources", entries)


def _article(
    rule: dict[str, Any],
    catalog: dict[str, Any],
    sutras: dict[str, Any],
    explorer: str,
    available_roots: set[str],
) -> str:
    rule_id = rule["id"]
    articles = {rid: entry for rid, entry in catalog["rules"].items() if rid != rule_id}
    engine = rule["engine"]
    kind = _KIND.get(rule["kind"], rule["kind"].capitalize())
    paragraphs = "".join(
        f"<p>{_reading(paragraph, articles)}</p>"
        for paragraph in rule["explanation"].strip().split("\n\n")
    )
    scope = (
        f'<p class="rule-scope"><strong>In the explorer.</strong> {_reading(engine["scope"], articles)}</p>'
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
        f"<h1>{escape(rule['text'])}</h1>"
        f'<p class="rule-gloss">{_reading(rule["gloss"], articles)}</p></header>'
        f'<section class="rule-explanation"><h2>How to read it</h2>{paragraphs}{scope}</section>'
        + _examples(rule["examples"], articles, explorer, available_roots)
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
        f"{_link(f'{rid}.html', rule['text'], 'rule-name')}"
        f'<p class="rule-gloss">{_reading(rule["gloss"], articles)}</p></li>'
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
