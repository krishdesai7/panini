import unicodedata
from panini.translit import iast_to_slp1, slp1_to_iast

def test_roundtrip_examples():
    for iast, slp in [("paṭhati", "paWati"), ("gacchati", "gacCati"), ("aidhata", "EData"),
                      ("bhavāmaḥ", "BavAmaH"), ("smṛ", "smf"), ("ṇīñ", "RIY"), ("ḍupacaṣ", "qupacaz"),
                      ("gamḷ~", "gamx~"), ("aṃ", "aM")]:
        assert iast_to_slp1(iast) == slp
        assert slp1_to_iast(slp) == iast

def test_decomposed_input_normalized():
    assert iast_to_slp1(unicodedata.normalize("NFD", "paṭh")) == "paW"
