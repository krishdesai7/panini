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


def test_render_explains_marker_notation():
    out = render_text(derive(parse_request("paṭh", "laṭ", 3, "sg", "active")))
    assert "capitals = markers (it)" in out.splitlines()[1]


def test_cli_exits_nonzero_when_derivation_errors(monkeypatch, capsys):
    import panini.engine as engine
    from panini.derivation import Derivation, Status
    monkeypatch.setattr(engine, "derive", lambda req, **kw: Derivation(
        {"root": "paṭh", "panini": "x"}, Status.ERROR, None, (), None, (), "boom"))
    assert main(["derive", "paṭh", "laṭ", "3", "sg"]) == 1
    assert "boom" in capsys.readouterr().out


def test_trace_has_no_bare_tildes():
    out = render_text(derive(parse_request("paṭh", "laṭ", 3, "sg", "active")))
    assert "~" not in out and "lãṭ" in out


def test_trace_flags_steps_that_leave_the_form_unchanged():
    out = render_text(derive(parse_request("bhū", "laṭ", 3, "sg", "active")))
    line = next(l for l in out.splitlines() if "1.3.78" in l and "śeṣāt" in l)
    assert "form unchanged" in out.splitlines()[out.splitlines().index(line) + 1]


def test_trace_prints_modern_terms_and_brackets_panini_s_at_v():
    d = derive(parse_request("bhū", "laṭ", 3, "sg", "active"))
    out = render_text(d)
    assert "{" not in out and "no rule assigns the middle voice" in out
    assert "no rule assigns the middle (ātmanepada) voice" in render_text(d, verbosity=1)


def test_multiline_notes_stay_aligned_in_the_trace():
    out = render_text(derive(parse_request("bhū", "laṭ", 3, "sg", "active"))).splitlines()
    k = next(i for i, l in enumerate(out) if "chosen by:" in l)
    indent = len(out[k]) - len(out[k].lstrip())
    assert all(len(l) - len(l.lstrip()) == indent for l in out[k + 1:k + 4])
