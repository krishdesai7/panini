"""All implemented rules, assembled from the rule modules."""

from panini.rules import anga, it, sandhi, tin
from panini.rules.base import Rule

ALL_RULES: tuple[Rule, ...] = (*it.RULES, *tin.RULES, *anga.RULES, *sandhi.RULES)

_BY_ID = {r.id: r for r in ALL_RULES}


def get_rule(rule_id: str) -> Rule:
    return _BY_ID[rule_id]
