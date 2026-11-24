"""The slice-1 lexicon: seven bhvādi roots, upadeśas as in Vidyut's dhātupāṭha (SLP1)."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Literal

from panini.translit import slp1_to_iast


@dataclass(frozen=True)
class Root:
    key: str
    upadesha: str  # SLP1, with ~ for nasal markers and \ ^ for accents
    gana: str
    meaning: str
    pada: Literal["P", "A", "U"]

    @property
    def upadesha_iast(self) -> str:
        return slp1_to_iast(self.upadesha.replace("\\", "").replace("^", ""))


ROOTS: dict[str, Root] = {
    r.key: r
    for r in (
        Root("bhū", "BU", "bhvādi", "to be, become", "P"),
        Root("paṭh", "paWa~", "bhvādi", "to speak clearly, recite", "P"),
        Root("gam", "ga\\mx~", "bhvādi", "to go", "P"),
        Root("smṛ", "smf\\", "bhvādi", "to remember", "P"),
        Root("edh", "eDa~\\", "bhvādi", "to grow, prosper", "A"),
        Root("nī", "RI\\Y", "bhvādi", "to lead", "U"),
        Root("pac", "qupa\\ca~^z", "bhvādi", "to cook", "U"),
    )
}


class UnknownRoot(LookupError):
    def __init__(self, text: str, available: tuple[str, ...]):
        self.text, self.available = text, available
        super().__init__(f"unknown root: {text!r}; available roots: {', '.join(available)}")


def lookup_root(text: str) -> Root:
    """Find a root by key or IAST upadeśa, ignoring Unicode form, spaces and a trailing hyphen."""
    norm = unicodedata.normalize("NFC", text).strip().removesuffix("-")
    for root in ROOTS.values():
        if norm in (root.key, root.upadesha_iast):
            return root
    raise UnknownRoot(text, tuple(ROOTS))
