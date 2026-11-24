"""Sound classes: pratyāhāras, savarṇa, guṇa and vṛddhi. All in SLP1."""

from functools import cache

# The fourteen Śiva sūtras (māheśvara sūtras). The last letter of each is the
# it marker that closes it; pratyāhāras are named by a first sound plus a marker.
SHIVA_SUTRAS: tuple[str, ...] = (
    "aiuR", "fxk", "eoN", "EOc", "hyvrw", "lR", "YmNRnm",
    "JBY", "GQDz", "jbgqdS", "KPCWTcwtv", "kpy", "Szsr", "hl",
)

SHORT_VOWELS = frozenset("aiufx")
LONG_OF = {"a": "A", "i": "I", "u": "U", "f": "F", "x": "X"}
SHORT_OF = {long: short for short, long in LONG_OF.items()}
VOWELS = frozenset("aAiIuUfFxXeEoO")

# Stop classes (varga): sounds in one varga share place and internal effort,
# so they are savarṇa with each other (1.1.9).
VARGAS: tuple[frozenset[str], ...] = (
    frozenset("kKgGN"), frozenset("cCjJY"), frozenset("wWqQR"),
    frozenset("tTdDn"), frozenset("pPbBm"),
)

_GUNA = {"a": "a", "A": "a", "i": "e", "I": "e", "u": "o", "U": "o",
         "f": "ar", "F": "ar", "x": "al", "X": "al",
         "e": "e", "E": "e", "o": "o", "O": "o"}  # nearest guṇa (1.1.50) for 6.1.87 with a following ec
_VRDDHI = {"a": "A", "A": "A", "i": "E", "I": "E", "u": "O", "U": "O",
           "f": "Ar", "F": "Ar", "x": "Al", "X": "Al",
           "e": "E", "E": "E", "o": "O", "O": "O"}


@cache
def pratyahara(name: str) -> frozenset[str]:
    """Expand a pratyāhāra name such as ``"ik"`` or ``"Jal"``.

    Markers are excluded. Short vowels include their long counterparts
    (1.1.69 aṇudit savarṇasya cāpratyayaḥ).
    """
    first, marker = name[:-1], name[-1]
    if len(first) == 2 and first[1] == "a":  # consonant + a for pronunciation: hal, yaY
        first = first[0]
    if name in ("cu", "wu"):  # the ku/cu/ṭu/tu/pu classes (1.1.69 udit)
        return next(v for v in VARGAS if name[0] in v)
    sounds: list[str] = []
    started = False
    for sutra in SHIVA_SUTRAS:
        body, end = sutra[:-1], sutra[-1]
        for c in body:
            if not started and c == first:
                started = True
            if started:
                sounds.append(c)
        if started and end == marker:
            break
    else:
        raise ValueError(f"unknown pratyāhāra: {name}")
    out = set(sounds)
    out |= {LONG_OF[c] for c in sounds if c in LONG_OF}
    return frozenset(out)


def is_vowel(c: str) -> bool:
    return c in VOWELS


def is_hrasva(c: str) -> bool:
    return c in SHORT_VOWELS


def dirgha(c: str) -> str:
    return LONG_OF.get(c, c)


def _vowel_class(c: str) -> str:
    base = SHORT_OF.get(c, c)
    return "f" if base == "x" else base  # ṛ and ḷ count as savarṇa (vārttika)


def is_savarna(a: str, b: str) -> bool:
    if is_vowel(a) or is_vowel(b):
        if a in "eEoO" or b in "eEoO":
            return a == b
        return is_vowel(a) and is_vowel(b) and _vowel_class(a) == _vowel_class(b)
    if a == b:
        return True
    return any(a in v and b in v for v in VARGAS)


def guna(c: str) -> str:
    """Guṇa replacement of a vowel (1.1.2), with r/l appended for ṛ/ḷ (1.1.51)."""
    return _GUNA[c]


def vrddhi(c: str) -> str:
    """Vṛddhi replacement of a vowel (1.1.1), with r/l appended for ṛ/ḷ (1.1.51)."""
    return _VRDDHI[c]
