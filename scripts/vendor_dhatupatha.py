"""Vendor the bhvādi section of Vidyut's dhātupāṭha into src/panini/data.

Run with `uv run --group dev python scripts/vendor_dhatupatha.py`. Keeps rows whose code starts
`01.` and whose dhātu is not `-` (a placeholder). Columns: code, dhatu (SLP1), artha (SLP1).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build/vidyut-data/prakriya/dhatupatha.tsv"
TARGET = ROOT / "src/panini/data/dhatupatha_bhvadi.tsv"


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    rows = [line for line in lines[1:] if line.startswith("01.") and line.split("\t")[1] != "-"]
    TARGET.write_text("code\tdhatu\tartha\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} roots to {TARGET}")


if __name__ == "__main__":
    main()
