"""Command line: `panini derive …` prints a derivation; `panini site` builds the explorer page."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from panini.lexicon import UnknownRoot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="panini", description="Watch Pāṇini's grammar derive verb forms.")
    sub = parser.add_subparsers(dest="command", required=True)

    d = sub.add_parser("derive", help="print the derivation of one form")
    d.add_argument("root", help="root, e.g. paṭh or bhū")
    d.add_argument("tense", help="present / past imperfective, or laṭ / laṅ")
    d.add_argument("person", help="3, 2, 1 or prathama, madhyama, uttama")
    d.add_argument("number", help="sg, du, pl or ekavacana, dvivacana, bahuvacana")
    d.add_argument("voice", nargs="?", default="active", help="active / middle, or parasmaipada / ātmanepada")
    d.add_argument("-v", "--verbose", action="count", default=0, help="-v: competitors; -vv: also before-forms")

    s = sub.add_parser("site", help="build the HTML explorer page")
    s.add_argument("--out", type=Path, default=Path("build/panini.html"))
    s.add_argument("--open", action="store_true", help="open the page in a browser")

    args = parser.parse_args(argv)
    try:
        if args.command == "derive":
            return _derive(args)
        return _site(args)
    except (UnknownRoot, ValueError) as e:
        print(f"panini: {e}", file=sys.stderr)
        return 2


def _derive(args: argparse.Namespace) -> int:
    from panini.engine import derive
    from panini.request import load_reference, parse_request
    from panini.trace import render_text

    req = parse_request(args.root, args.tense, args.person, args.number, args.voice)
    print(render_text(derive(req, reference=load_reference()), verbosity=args.verbose))
    return 0


def _site(args: argparse.Namespace) -> int:
    from panini.site.build import build_site

    out = build_site(args.out)
    print(f"wrote {out}")
    if args.open:
        import webbrowser
        webbrowser.open(out.resolve().as_uri())
    return 0
