"""What the user asks for, in PIE-style or Pāṇinian terms, and how it maps to intent."""

from __future__ import annotations

import json
import sys
import unicodedata
from dataclasses import dataclass
from enum import Enum
from functools import cache
from pathlib import Path
lazy from collections.abc import Iterable

from panini.lexicon import ROOTS, Root, lookup_root, middle_voice_reason
from panini.model import Coreference, Intent, Number, Term, TermKind, Time


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


_PURUSHA_NAME = {
    Purusha.PRATHAMA: "prathama",
    Purusha.MADHYAMA: "madhyama",
    Purusha.UTTAMA: "uttama",
}
_VACANA_NAME = {
    Vacana.EKA: "ekavacana",
    Vacana.DVI: "dvivacana",
    Vacana.BAHU: "bahuvacana",
}
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
            coreference={
                Purusha.PRATHAMA: Coreference.NONE,
                Purusha.MADHYAMA: Coreference.ADDRESSEE,
                Purusha.UTTAMA: Coreference.SPEAKER,
            }[self.purusha],
            number={
                Vacana.EKA: Number.ONE,
                Vacana.DVI: Number.TWO,
                Vacana.BAHU: Number.MANY,
            }[self.vacana],
            fruit_to_agent=self.voice is Voice.MIDDLE,
        )

    @property
    def pada_letter(self) -> str:
        return "P" if self.voice is Voice.ACTIVE else "Ā"

    @property
    def key(self) -> str:
        return f"{self.root.code}|{self.lakara.iast}|{self.pada_letter}|{self.purusha.value}|{self.vacana.value}"

    def describe(self) -> tuple[str, str]:
        panini = (
            f"{self.lakara.iast} · {_PURUSHA_NAME[self.purusha]} puruṣa {_VACANA_NAME[self.vacana]}"
            f" · {_PADA_NAME[self.voice]}"
        )
        pie = f"{self.purusha.value}{self.vacana.value} {self.lakara.pie} {self.voice.value}"
        return panini, pie


def _norm(s: str | int) -> str:
    return unicodedata.normalize("NFC", str(s)).strip().lower()


_TENSES = {
    **dict.fromkeys(["laṭ", "lat", "present", "present imperfective"], Lakara.LAT),
    **dict.fromkeys(
        ["laṅ", "lan", "imperfect", "past", "past imperfective"], Lakara.LAN
    ),
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
        raise ValueError(
            f"unknown {what} {value!r}; use one of: {', '.join(table)}"
        ) from None


def parse_request(
    root: str, tense: str, person: str | int, number: str, voice: str = "active"
) -> Request:
    return Request(
        root=lookup_root(root),
        lakara=_pick(_TENSES, tense, "tense"),
        purusha=_pick(_PERSONS, person, "person"),
        vacana=_pick(_NUMBERS, number, "number"),
        voice=_pick(_VOICES, voice, "voice"),
    )


_NU = "deferred to the athematic classes"
_TWO = "the engine would show only one, so it waits for optional rules"
_DESID = "takes a desiderative stem here, which this engine doesn't derive yet"

# Roots of the bhvādi and tudādi sections whose laṭ/laṅ stems need machinery outside this slice:
# code -> (reason, governing sūtra).
OUT_OF_SCOPE: dict[str, tuple[str, str]] = {
    "01.1092": (f"śru forms a nu-present (śṛṇoti), {_NU}", "3.1.74"),
    "01.0677": (f"dhinv forms a nu-present (dhinoti), {_NU}", "3.1.80"),
    "01.0682": (f"kṛṇv forms a nu-present (kṛṇoti), {_NU}", "3.1.80"),
    "01.0461": (
        "gup takes the suffix -āya- (gopāyati), which this engine doesn't derive yet",
        "3.1.28",
    ),
    "01.0462": (
        "dhūp takes the suffix -āya- (dhūpāyati), which this engine doesn't derive yet",
        "3.1.28",
    ),
    "01.0511": (
        "kam takes the suffix ṇiṅ (kāmayate), which this engine doesn't derive yet",
        "3.1.30",
    ),
    "01.0545": (
        "kram preferably takes -ya- in the middle voice, an option this engine doesn't model yet",
        "3.1.70",
    ),
    "01.0507": (
        "paṇ takes the suffix -āya- (paṇāyati), which this engine doesn't derive yet",
        "3.1.28",
    ),
    "01.0508": (
        "pan takes the suffix -āya- (panāyati), which this engine doesn't derive yet",
        "3.1.28",
    ),
    "06.0102": (f"truṭ has two present stems, truṭyati and truṭati; {_TWO}", "3.1.70"),
    "06.0159": (
        "vich takes the suffix -āya- (vicchāyati), which this engine doesn't derive yet",
        "3.1.28",
    ),
    "01.1166": (
        "ṛti takes the suffix -īya- (ṛtīyate), which this engine doesn't derive yet",
        "3.1.29",
    ),
    "01.0742": (f"akṣ has two present stems, akṣṇoti and akṣati; {_TWO}", "3.1.75"),
    "01.0743": (f"takṣ has two present stems, takṣṇoti and takṣati; {_TWO}", "3.1.75"),
    "01.0958": (
        f"bhrāś has two present stems, bhrāśyate and bhrāśate; {_TWO}",
        "3.1.70",
    ),
    "01.0959": (
        f"bhlāś has two present stems, bhlāśyate and bhlāśate; {_TWO}",
        "3.1.70",
    ),
    "01.0985": (
        f"bhram has two present stems, bhramyati and bhramati; {_TWO}",
        "3.1.70",
    ),
    "01.1033": (f"laṣ has two present stems, laṣyati and laṣati; {_TWO}", "3.1.70"),
    "01.1125": (f"gup {_DESID} (jugupsate)", "3.1.5"),
    "01.1126": (f"tij {_DESID} (titikṣate)", "3.1.5"),
    "01.1127": (f"mān {_DESID} (mīmāṃsate)", "3.1.6"),
    "01.1128": (f"badh {_DESID} (bībhatsate)", "3.1.6"),
    "01.1148": (f"kit {_DESID} (cikitsati)", "3.1.5"),
    "01.1149": (f"dān {_DESID} (dīdāṃsate)", "3.1.6"),
    "01.1150": (f"śān {_DESID} (śīśāṃsate)", "3.1.6"),
    # Kṣīrataraṅgiṇī I.415: "jabha jṛbhi gātravināme. jabhate"; Vidyut's jabhati (active) is attested
    # nowhere, so there is no reference to derive against (docs/findings.md).
    "01.0150": (
        (
            "this jabh is Kṣīrasvāmin's reading (jabha) of jabhī, 01.0453. He conjugates it jabhate: "
            "middle voice, and without the nasal that 7.1.61 adds before a vowel. The sūtra as worded "
            "doesn't give that form, so the entry is left out"
        ),
        "7.1.61",
    ),
}


# Roots whose voice a sūtra fixes beyond what their markers say: sūtra -> (voice, root codes).
VOICE_BY_SUTRA: dict[str, tuple[Voice, tuple[str, ...]]] = {
    "1.3.60": (
        Voice.MIDDLE,
        ("01.0991", "06.0164"),
    ),  # śad (in bhvādi and tudādi) takes ātmanepada before an affix marked ś
}


def voice_set_by(root: Root) -> tuple[str, Voice] | None:
    """(sūtra, voice) if one of VOICE_BY_SUTRA fixes this root's voice."""
    return next(
        (
            (rule, voice)
            for rule, (voice, codes) in VOICE_BY_SUTRA.items()
            if root.code in codes
        ),
        None,
    )


def effective_pada(root: Root) -> str:
    """Root.pada, corrected by VOICE_BY_SUTRA."""
    fixed = voice_set_by(root)
    return root.pada if fixed is None else ("A" if fixed[1] is Voice.MIDDLE else "P")


def availability(req: Request) -> tuple[str, str] | None:
    """Why a request has no form, as (reason, governing rule), or None if it has one."""
    if req.root.code in OUT_OF_SCOPE:
        return OUT_OF_SCOPE[req.root.code]
    if (fixed := voice_set_by(req.root)) is not None:
        rule, voice = fixed
        if req.voice is not voice:
            return (
                f"{req.root.name} takes ātmanepada before an affix marked ś, as in laṭ and laṅ",
                rule,
            )
        return None
    if req.root.pada == "P" and req.voice is Voice.MIDDLE:
        return (f"{req.root.name} takes parasmaipada only", "1.3.78")
    if req.root.pada == "A" and req.voice is Voice.ACTIVE:
        reason = middle_voice_reason(
            Term.from_upadesha(TermKind.ROOT, req.root.upadesha), "it", markup=False
        )
        return (f"{req.root.name} takes ātmanepada only: {reason}", "1.3.12")
    return None


def all_requests(codes: Iterable[str] | None = None) -> list[Request]:
    """Every request for the given root codes (default: the whole lexicon)."""
    roots = ROOTS.values() if codes is None else [ROOTS[c] for c in codes]
    return [
        Request(root, lakara, purusha, vacana, voice)
        for root in roots
        for lakara in Lakara
        for voice in Voice
        for purusha in Purusha
        for vacana in Vacana
    ]


REFERENCE_PATH = Path(__file__).parent / "data" / "reference_forms.json"


@cache
def load_reference(path: Path = REFERENCE_PATH) -> dict[str, list[str]]:
    """Reference forms keyed by Request.key (generated from Vidyut by scripts/make_reference.py).

    Missing file: warns on stderr and returns {}, since without it the GUI can't flag
    forms that disagree with the reference.
    """
    if not path.exists():
        print(  # ruff: ignore[print]
            f"warning: reference forms not found at {path}; mismatches will not be flagged",
            file=sys.stderr,
        )
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
