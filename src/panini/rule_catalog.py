"""Build rule articles from editorial notes and the current engine."""

import tomllib
from dataclasses import dataclass, field
from importlib.resources import files
from typing import Any

from panini.derivation import Status
from panini.engine import derive
from panini.request import parse_request
from panini.rules import ALL_RULES
from panini.rules.base import sutra_info
from panini.rules.readings import PARIBHASHA, READS


@dataclass(frozen=True)
class _Article:
    kind: str
    explanation: str
    citations: list[dict[str, str]]
    scope: str | None = None
    related: dict[str, str] = field(default_factory=dict)
    examples: list[dict[str, Any]] = field(default_factory=list)


def _known_sutra(rule_id: str) -> tuple[str, str]:
    if not rule_id.startswith("9.9."):
        try:
            return sutra_info(rule_id)
        except KeyError:
            pass
    raise ValueError(f"unknown sūtra {rule_id!r}")


def _example(
    rule_id: str,
    *,
    request: dict[str, Any],
    note: str,
    step_rule: str | None = None,
    occurrence: int | None = None,
) -> dict[str, Any]:
    selected = step_rule or rule_id
    req = parse_request(**request)
    label = f"{rule_id} example {req.key} (step {selected})"
    derivation = derive(req)
    if derivation.status is not Status.OK:
        raise ValueError(f"{label}: {derivation.message or derivation.status.value}")

    matches = [
        (number, step)
        for number, step in enumerate(derivation.steps, start=1)
        if selected in step.rule_ids
    ]
    if occurrence is None:
        if len(matches) != 1:
            raise ValueError(
                f"{label}: expected one matching step, found {len(matches)}"
            )
        occurrence = 1
    if not 1 <= occurrence <= len(matches):
        raise ValueError(f"{label}: occurrence {occurrence} out of {len(matches)}")
    number, step = matches[occurrence - 1]
    return {
        "request": derivation.request,
        "result": derivation.result,
        "note": note,
        "step_rule": selected,
        "step_number": number,
        "step": step.to_json(),
    }


def _build_article(
    rule_id: str, article: _Article, sources: dict[str, Any]
) -> dict[str, Any]:
    text, gloss = _known_sutra(rule_id)
    for related_id in article.related:
        _known_sutra(related_id)
    for citation in article.citations:
        if citation["source"] not in sources:
            raise ValueError(f"{rule_id}: unknown source {citation['source']!r}")

    operation = next((rule for rule in ALL_RULES if rule.id == rule_id), None)
    return {
        "id": rule_id,
        "text": text,
        "gloss": gloss,
        "kind": article.kind,
        "explanation": article.explanation,
        "citations": article.citations,
        "related": article.related,
        "engine": {
            "scope": article.scope,
            "registered_operation": operation is not None,
            "blocks": list(operation.blocks) if operation else [],
            "blocked_by": [rule.id for rule in ALL_RULES if rule_id in rule.blocks],
            "readings": [
                {
                    "id": source,
                    "kind": "maxim" if source in PARIBHASHA else "sutra",
                    "note": note,
                }
                for source, note in READS.get(rule_id, ())
            ],
        },
        "examples": [_example(rule_id, **example) for example in article.examples],
    }


def build_catalog(rule_id: str | None = None) -> dict[str, Any]:
    """Build JSON-ready rule data, optionally restricted to one article."""
    resource = files("panini.data").joinpath("rule_articles.toml")
    data = tomllib.loads(resource.read_text(encoding="utf-8"))
    sources = data["sources"]
    articles = data["articles"]
    if rule_id is not None and rule_id not in articles:
        raise ValueError(f"no rule article for {rule_id}")
    ids = (
        [rule_id]
        if rule_id is not None
        else sorted(articles, key=lambda value: tuple(map(int, value.split("."))))
    )
    return {
        "schema_version": 1,
        "sources": sources,
        "rules": {
            rid: _build_article(rid, _Article(**articles[rid]), sources) for rid in ids
        },
    }
