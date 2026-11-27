"""Vidyut's Gana for one of our gaṇa names (dev-only; shared by the scripts that call Vidyut)."""

import unicodedata

from vidyut.prakriya import Gana

from panini.lexicon import GANAS


def vidyut_gana(gana: str) -> Gana:
    """bhvādi -> Gana.Bhvadi, tudādi -> Gana.Tudadi: Vidyut names its gaṇas in plain ASCII."""
    if gana not in GANAS.values():
        raise ValueError(f"not a gaṇa in the lexicon: {gana!r}")
    ascii_name = unicodedata.normalize("NFD", gana).encode("ascii", "ignore").decode()
    return getattr(Gana, ascii_name.capitalize())
