"""Vendor the bhvādi and tudādi sections of Vidyut's dhātupāṭha into src/panini/data.

Run with `uv run --group dev python scripts/vendor_dhatupatha.py`. Keeps rows whose code starts
with the section's prefix (`01.`, `06.`) and whose dhātu is not `-` (a placeholder). Columns:
code, dhatu (SLP1), artha (SLP1).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build/vidyut-data/prakriya/dhatupatha.tsv"
DATA = ROOT / "src/panini/data"
# list-code prefix -> vendored file
SECTIONS = {"01": "dhatupatha_bhvadi.tsv", "06": "dhatupatha_tudadi.tsv"}

# Entries that are not recited upadeśas, rewritten as one. Vidyut special-cases the same entry
# (vidyut-prakriya/src/dhatu_karya.rs, "an anomalous root from our dhatupatha"), reading the root
# as bare chad with no markers.
# - CadiH (01.0925): the root chad cited by name, chadiḥ (chad + ik in the nominative, as roots
#   are named by the vārttika ik-śtipau dhātunirdeśe on 3.3.108), not recited with its markers.
#   As an upadeśa it is chad with the plain marker vowel: parasmaipada (1.3.78), no nasal (not
#   idit), so chadati, as Vidyut derives.
# - yuCa~ (01.0242) and uCI~ (01.0244): stored with the t already inserted, yucCa~ and ucCI~.
#   The upadeśas have a single ch; the printed lists write yuccha and ucchī only because 6.1.73
#   che ca applies in recitation. In a derivation, 6.1.73 (t after a short vowel before ch) and
#   7.3.86 (full grade of a light penultimate vowel) each remove the other's context, and neither
#   nitya nor the siddha principle decides between them (Kiparsky, "Pāṇini is slick", on ṛch), so
#   the grammar alone predicts *yocchati as readily as yucchati. Storing the cch is a stipulation
#   that closes this gap, not a traditional reading. It can't be extended to every root in ch:
#   prach must keep a single ch for 6.4.19 chvoḥ śūḍ anunāsike ca (praśna). See docs/findings.md.
#   Tudādi uch (06.0015) and ṛch (06.0016) keep their single ch: before śa, which counts as
#   marked ṅ (1.2.4), 1.1.5 blocks full grade, so 6.1.73 has no rival and the trace shows it.
# Keyed by list code, not spelling: the same upadeśa (uCI~) recurs in other sections.
READINGS = {"01.0925": "Cada~", "01.0242": "yucCa~", "01.0244": "ucCI~"}


def _read(line: str) -> str:
    code, dhatu, artha = line.split("\t")
    return "\t".join((code, READINGS.get(code, dhatu), artha))


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    for prefix, name in SECTIONS.items():
        rows = [
            _read(line)
            for line in lines[1:]
            if line.startswith(f"{prefix}.") and line.split("\t")[1] != "-"
        ]
        target = DATA / name
        target.write_text(
            "code\tdhatu\tartha\n" + "\n".join(rows) + "\n", encoding="utf-8"
        )
        print(f"wrote {len(rows)} roots to {target}")


if __name__ == "__main__":
    main()
