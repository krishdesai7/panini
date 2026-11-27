"""CLI: `panini derive …` prints derivation; `panini site` builds the explorer page."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, NoReturn
lazy from http.server import ThreadingHTTPServer

import typer
from rich.console import Console

from .lexicon import UnknownRoot
lazy from .derivation import Derivation
lazy from .request import Request

app = typer.Typer(
    name="panini",
    help="Watch Pāṇini's grammar derive verb forms.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console(highlight=False)
err_console = Console(stderr=True, highlight=False)

NoCache = Annotated[
    bool,
    typer.Option(
        "--no-cache", help="Derive everything; don't read or write the cache."
    ),
]
OpenBrowser = Annotated[
    bool, typer.Option("--open", help="Open the page in a browser.")
]


def _fail(message: str, code: int = 2) -> NoReturn:
    err_console.print(f"[bold red]panini:[/] {message}", markup=True, soft_wrap=True)
    raise typer.Exit(code)


@app.command()
def derive(
    root: Annotated[str, typer.Argument(help="Root, e.g. paṭh or bhū.")],
    tense: Annotated[
        str, typer.Argument(help="present / past imperfective, or laṭ / laṅ.")
    ],
    person: Annotated[
        str, typer.Argument(help="3, 2, 1 or prathama, madhyama, uttama.")
    ],
    number: Annotated[
        str,
        typer.Argument(help="sg, du, pl or ekavacana, dvivacana, bahuvacana."),
    ],
    voice: Annotated[
        str,
        typer.Argument(help="active / middle, or parasmaipada / ātmanepada."),
    ] = "active",
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            show_default=False,
            help="-v: competitors; -vv: also before-forms.",
        ),
    ] = 0,
) -> None:
    """Print the derivation of one form."""
    from panini import engine
    from panini.derivation import Status
    from panini.request import load_reference, parse_request
    from panini.trace import render_text

    try:
        req: Request = parse_request(root, tense, person, number, voice)
    except (UnknownRoot, ValueError) as e:
        _fail(str(e))
    d: Derivation = engine.derive(req, reference=load_reference())
    # The trace is aligned plain text: keep Rich from wrapping or styling it.
    typer.echo(render_text(d, verbosity=verbose))
    if d.status is Status.ERROR:
        raise typer.Exit(1)


@app.command()
def rules(
    rule_id: Annotated[
        str | None, typer.Argument(help="Optional sūtra number, e.g. 1.1.1.")
    ] = None,
) -> None:
    """Export rule articles as JSON."""
    import json

    from panini.rule_catalog import build_catalog

    try:
        catalog = build_catalog(rule_id)
    except ValueError as e:
        _fail(str(e))
    typer.echo(json.dumps(catalog, ensure_ascii=False, indent=2))


@app.command()
def site(
    out: Annotated[Path, typer.Option(help="Where to write the page.")] = Path(
        "build/panini.html"
    ),
    open_: OpenBrowser = False,
    no_cache: NoCache = False,
) -> None:
    """Build the HTML explorer page."""
    from panini.site.build import build_site, use_disk_cache

    use_disk_cache(not no_cache)
    with console.status("deriving every root…"):
        written: Path = build_site(out)
    console.print(f"[green]wrote[/] {written}")
    if open_:
        import webbrowser

        webbrowser.open(written.resolve().as_uri())


@app.command()
def serve(
    port: Annotated[int, typer.Option(help="Port to listen on.")] = 8000,
    open_: OpenBrowser = False,
    no_cache: NoCache = False,
) -> None:
    """Serve the explorer locally, deriving one root at a time."""
    from panini.site.build import use_disk_cache
    from panini.site.serve import make_server

    use_disk_cache(not no_cache)
    try:
        server: ThreadingHTTPServer = make_server(port=port)
    except OSError as e:
        _fail(f"cannot bind port {port}: {e}")
    url: str = f"http://127.0.0.1:{server.server_address[1]}/"
    console.print(f"serving [link={url}]{url}[/link] [dim](Ctrl-C to stop)[/]")
    if open_:
        import webbrowser

        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
