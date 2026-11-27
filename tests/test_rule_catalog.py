import json

import pytest
from typer.testing import CliRunner

from panini.cli import app
from panini.rule_catalog import _example, build_catalog


def test_catalog_keeps_a_definition_distinct_from_its_worked_example() -> None:
    catalog = build_catalog()
    definition = catalog["rules"]["1.1.1"]
    (example,) = definition["examples"]

    assert definition["kind"] == "definition"
    assert not definition["engine"]["registered_operation"]
    assert example["step"]["rule_ids"] == ["6.1.90"]
    assert example["request"]["key"] == "01.1086|laṅ|P|3|sg"
    assert example["result"] == "ārcchat"
    assert "6.1.90" in catalog["rules"]
    assert "1.1.3" in definition["related"]
    assert "1.1.3" not in catalog["rules"]


def test_operation_article_includes_its_scope_and_engine_evidence() -> None:
    article = build_catalog("7.3.84")["rules"]["7.3.84"]
    (example,) = article["examples"]

    assert article["engine"]["registered_operation"]
    assert "1.1.5" in article["engine"]["blocked_by"]
    assert "sārvadhātuka" in article["engine"]["scope"]
    assert example["step"]["before"][0]["iast"] == "bhū"
    assert example["step"]["after"][0]["iast"] == "bho"
    assert example["result"] == "bhavati"


def test_export_rejects_an_example_without_its_selected_step() -> None:
    with pytest.raises(
        ValueError, match=r"6\.1\.90\): expected one matching step, found 0"
    ):
        _example(
            "1.1.1",
            request={"root": "01.0001", "tense": "laṭ", "person": 3, "number": "sg"},
            step_rule="6.1.90",
            note="",
        )


def test_rules_cli_exports_a_single_article() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["rules", "1.1.1"])
    assert result.exit_code == 0
    catalog = json.loads(result.stdout)
    assert catalog["schema_version"] == 1
    assert list(catalog["rules"]) == ["1.1.1"]

    result = runner.invoke(app, ["rules", "1.1.3"])
    assert result.exit_code == 2
    assert "no rule article for 1.1.3" in result.stderr
