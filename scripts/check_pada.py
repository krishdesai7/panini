"""Cross-check Root.pada against Vidyut (dev-only): which voices does Vidyut derive for laṭ 3sg?

Run with:  uv run --group dev python scripts/check_pada.py
Disagreements are recorded in docs/findings.md.
"""

from panini.lexicon import ROOTS
from vidyut.prakriya import (
    Dhatu,
    DhatuPada,
    Gana,
    Lakara,
    Pada,
    Prayoga,
    Purusha,
    Vacana,
    Vyakarana,
)


def vidyut_pada(v: Vyakarana, upadesha: str) -> str:
    dhatu = Dhatu.mula(aupadeshika=upadesha, gana=Gana.Bhvadi)
    have = ""
    for letter, dp in (("P", DhatuPada.Parasmaipada), ("A", DhatuPada.Atmanepada)):
        pada = Pada.Tinanta(
            dhatu=dhatu,
            prayoga=Prayoga.Kartari,
            lakara=Lakara.Lat,
            purusha=Purusha.Prathama,
            vacana=Vacana.Eka,
            dhatu_pada=dp,
        )
        if v.derive(pada):
            have += letter
    return {"P": "P", "A": "A", "PA": "U", "": "none"}[have]


def main() -> None:
    v = Vyakarana()
    bad = [
        (r, got)
        for r in ROOTS.values()
        if (got := vidyut_pada(v, r.upadesha)) != r.pada
    ]
    for _r, got in bad:
        pass


if __name__ == "__main__":
    main()
