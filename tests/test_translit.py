import unicodedata
from panini.translit import iast_to_slp1, slp1_to_iast

def test_roundtrip_examples() -> None:
    for iast, slp in [("paṭhati", "paWati"), ("gacchati", "gacCati"), ("aidhata", "EData"),
                      ("bhavāmaḥ", "BavAmaH"), ("smṛ", "smf"), ("ṇīñ", "RIY"), ("ḍupacaṣ", "qupacaz"),
                      ("gamḷ̃", "gamx~"), ("paṭhã", "paWa~"), ("aṃ", "aM")]:
        assert iast_to_slp1(iast) == slp
        assert slp1_to_iast(slp) == iast

def test_decomposed_input_normalized() -> None:
    assert iast_to_slp1(unicodedata.normalize("NFD", "paṭh")) == "paW"


def test_nasal_vowel_displays_with_a_tilde_over_it() -> None:
    assert slp1_to_iast("la~w") == "lãṭ"
    assert "~" not in slp1_to_iast("ru~")
