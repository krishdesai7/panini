"""Entry point for both the `panini` script and `python -m panini`."""

from .cli import app


def main() -> None:
    app(prog_name="panini")


if __name__ == "__main__":
    main()
