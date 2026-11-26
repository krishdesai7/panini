"""Generate src/panini/data/reference_forms.json from Vidyut (dev-only).

Vidyut (Ambuda's Pāṇinian engine) serves as an independent cross-check, not
ground truth. Run with:  uv run --group dev scripts/make_reference.py
"""

import json
from pathlib import Path

import vidyut
from panini import request as rq
from panini.request import all_requests, availability
from vidyut.lipi import Scheme, transliterate
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

DATA = Path("build/vidyut-data")
OUT = Path("src/panini/data/reference_forms.json")

LAKARA = {rq.Lakara.LAT: Lakara.Lat, rq.Lakara.LAN: Lakara.Lan}
PURUSHA = {
    rq.Purusha.PRATHAMA: Purusha.Prathama,
    rq.Purusha.MADHYAMA: Purusha.Madhyama,
    rq.Purusha.UTTAMA: Purusha.Uttama,
}
VACANA = {
    rq.Vacana.EKA: Vacana.Eka,
    rq.Vacana.DVI: Vacana.Dvi,
    rq.Vacana.BAHU: Vacana.Bahu,
}
PADA = {rq.Voice.ACTIVE: DhatuPada.Parasmaipada, rq.Voice.MIDDLE: DhatuPada.Atmanepada}


def main() -> None:
    if not DATA.exists():
        vidyut.download_data(str(DATA))
    v = Vyakarana()
    out: dict[str, list[str]] = {}
    for req in all_requests():
        if availability(req) is not None:
            continue
        dhatu = Dhatu.mula(aupadeshika=req.root.upadesha, gana=Gana.Bhvadi)
        pada = Pada.Tinanta(
            dhatu=dhatu,
            prayoga=Prayoga.Kartari,
            lakara=LAKARA[req.lakara],
            purusha=PURUSHA[req.purusha],
            vacana=VACANA[req.vacana],
            dhatu_pada=PADA[req.voice],
        )
        forms = [
            transliterate(p.text, Scheme.Slp1, Scheme.Iast) for p in v.derive(pada)
        ]
        out[req.key] = list(dict.fromkeys(forms))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(dict(sorted(out.items())), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(out)} entries to {OUT}")


if __name__ == "__main__":
    main()
