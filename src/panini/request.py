"""What the user asks for, in PIE-style or Pāṇinian terms, and how it maps to intent."""

from __future__ import annotations

import json
import sys
import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from panini.lexicon import ROOTS, Root, lookup_root
from panini.model import Coreference, Intent, Number, Time


class Lakara(Enum):
    LAT = "laṭ"
    LAN = "laṅ"

    @property
    def iast(self) -> str:
        return self.value

    @property
    def pie(self) -> str:
        return "present imperfective" if self is Lakara.LAT else "past imperfective"


class Purusha(Enum):
    PRATHAMA = 3
    MADHYAMA = 2
    UTTAMA = 1


class Vacana(Enum):
    EKA = "sg"
    DVI = "du"
    BAHU = "pl"


class Voice(Enum):
    ACTIVE = "active"
    MIDDLE = "middle"


_PURUSHA_NAME = {Purusha.PRATHAMA: "prathama", Purusha.MADHYAMA: "madhyama", Purusha.UTTAMA: "uttama"}
_VACANA_NAME = {Vacana.EKA: "ekavacana", Vacana.DVI: "dvivacana", Vacana.BAHU: "bahuvacana"}
_PADA_NAME = {Voice.ACTIVE: "parasmaipada", Voice.MIDDLE: "ātmanepada"}


@dataclass(frozen=True)
class Request:
    root: Root
    lakara: Lakara
    purusha: Purusha
    vacana: Vacana
    voice: Voice

    def intent(self) -> Intent:
        return Intent(
            time=Time.PRESENT if self.lakara is Lakara.LAT else Time.PAST_NOT_TODAY,
            coreference={Purusha.PRATHAMA: Coreference.NONE, Purusha.MADHYAMA: Coreference.ADDRESSEE,
                         Purusha.UTTAMA: Coreference.SPEAKER}[self.purusha],
            number={Vacana.EKA: Number.ONE, Vacana.DVI: Number.TWO, Vacana.BAHU: Number.MANY}[self.vacana],
            fruit_to_agent=self.voice is Voice.MIDDLE,
        )

    @property
    def pada_letter(self) -> str:
        return "P" if self.voice is Voice.ACTIVE else "Ā"

    @property
    def key(self) -> str:
        return f"{self.root.code}|{self.lakara.iast}|{self.pada_letter}|{self.purusha.value}|{self.vacana.value}"

    def describe(self) -> tuple[str, str]:
        panini = (f"{self.lakara.iast} · {_PURUSHA_NAME[self.purusha]} puruṣa {_VACANA_NAME[self.vacana]}"
                  f" · {_PADA_NAME[self.voice]}")
        pie = f"{self.purusha.value}{self.vacana.value} {self.lakara.pie} {self.voice.value}"
        return panini, pie


def _norm(s: str | int) -> str:
    return unicodedata.normalize("NFC", str(s)).strip().lower()


_TENSES = {
    **dict.fromkeys(["laṭ", "lat", "present", "present imperfective"], Lakara.LAT),
    **dict.fromkeys(["laṅ", "lan", "imperfect", "past", "past imperfective"], Lakara.LAN),
}
_PERSONS = {
    **dict.fromkeys(["3", "prathama"], Purusha.PRATHAMA),
    **dict.fromkeys(["2", "madhyama"], Purusha.MADHYAMA),
    **dict.fromkeys(["1", "uttama"], Purusha.UTTAMA),
}
_NUMBERS = {
    **dict.fromkeys(["sg", "eka", "ekavacana"], Vacana.EKA),
    **dict.fromkeys(["du", "dvi", "dvivacana"], Vacana.DVI),
    **dict.fromkeys(["pl", "bahu", "bahuvacana"], Vacana.BAHU),
}
_VOICES = {
    **dict.fromkeys(["active", "parasmaipada", "p"], Voice.ACTIVE),
    **dict.fromkeys(["middle", "ātmanepada", "atmanepada", "a", "ā"], Voice.MIDDLE),
}


def _pick[T](table: dict[str, T], value: str | int, what: str) -> T:
    try:
        return table[_norm(value)]
    except KeyError:
        raise ValueError(f"unknown {what} {value!r}; use one of: {', '.join(table)}") from None


def parse_request(root: str, tense: str, person: str | int, number: str, voice: str = "active") -> Request:
    return Request(
        root=lookup_root(root),
        lakara=_pick(_TENSES, tense, "tense"),
        purusha=_pick(_PERSONS, person, "person"),
        vacana=_pick(_NUMBERS, number, "number"),
        voice=_pick(_VOICES, voice, "voice"),
    )


def availability(req: Request) -> tuple[str, str] | None:
    """Why a request has no form, as (reason, governing rule), or None if it has one."""
    if req.root.pada == "P" and req.voice is Voice.MIDDLE:
        return (f"{req.root.name} takes parasmaipada only", "1.3.78")
    if req.root.pada == "A" and req.voice is Voice.ACTIVE:
        return (f"{req.root.name} takes ātmanepada only: its marker vowel is anudātta", "1.3.12")
    return None


def all_requests() -> list[Request]:
    return [
        Request(root, lakara, purusha, vacana, voice)
        for root in ROOTS.values()
        for lakara in Lakara
        for voice in Voice
        for purusha in Purusha
        for vacana in Vacana
    ]


REFERENCE_PATH = Path(__file__).parent / "data" / "reference_forms.json"


def load_reference(path: Path = REFERENCE_PATH) -> dict[str, list[str]]:
    """Reference forms keyed by Request.key (generated from Vidyut by scripts/make_reference.py).

    Missing file: warns on stderr and returns {}, since without it the GUI can't flag
    forms that disagree with the reference.
    """
    if not path.exists():
        print(f"warning: reference forms not found at {path}; mismatches will not be flagged", file=sys.stderr)
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
