"""Vendor the bhvādi section of Vidyut's dhātupāṭha into src/panini/data.

Run with `uv run --group dev python scripts/vendor_dhatupatha.py`. Keeps rows whose code starts
`01.` and whose dhātu is not `-` (a placeholder). Columns: code, dhatu (SLP1), artha (SLP1).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build/vidyut-data/prakriya/dhatupatha.tsv"
TARGET = ROOT / "src/panini/data/dhatupatha_bhvadi.tsv"

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
READINGS = {"CadiH": "Cada~", "yuCa~": "yucCa~", "uCI~": "ucCI~"}


def _read(line: str) -> str:
    code, dhatu, artha = line.split("\t")
    return "\t".join((code, READINGS.get(dhatu, dhatu), artha))


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    rows = [_read(line) for line in lines[1:] if line.startswith("01.") and line.split("\t")[1] != "-"]
    TARGET.write_text("code\tdhatu\tartha\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} roots to {TARGET}")


if __name__ == "__main__":
    main()
