# tests/test_trace_cli.py
from panini.cli import main
from panini.engine import derive
from panini.request import parse_request
from panini.trace import render_text

def test_render_default_and_verbose():
    d = derive(parse_request("bhū", "laṭ", 3, "pl", "active"))
    out = render_text(d)
    assert out.splitlines()[0].endswith("→  bhavanti") and "6.1.97" in out and "✗" not in out
    assert "✗ 6.1.101" in render_text(d, verbosity=1)

def test_cli_derive(capsys):
    assert main(["derive", "paṭh", "present", "3", "sg"]) == 0
    assert "paṭhati" in capsys.readouterr().out

def test_cli_unknown_root(capsys):
    assert main(["derive", "kṛ", "laṭ", "3", "sg"]) == 2
    err = capsys.readouterr().err
    assert "kṛ" in err and "bhū" in err and "Traceback" not in err
