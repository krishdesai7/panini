from panini.sounds import pratyahara, is_savarna, guna, vrddhi, dirgha

def test_pratyaharas() -> None:
    assert pratyahara("ik") == frozenset("iufx") | frozenset("IUFX")   # 1.1.69 savarṇa-inclusive
    assert "a" not in pratyahara("ik")
    assert pratyahara("Jal") >= frozenset("JBGQDjbgqdKPCWTcwtkpSzsh")
    assert pratyahara("yaY") == frozenset("yvrlYmNRnJB")   # yañ: y … ñ of Śiva sūtra 8
    assert pratyahara("val") == pratyahara("hal") - {"y"}

def test_guna_vrddhi() -> None:
    assert [guna(c) for c in "iIuUfF"] == ["e", "e", "o", "o", "ar", "ar"]   # 1.1.51 uraṇ raparaḥ
    assert vrddhi("e") == "E" and vrddhi("a") == "A"

def test_savarna_and_dirgha() -> None:
    assert is_savarna("a", "A") and not is_savarna("a", "i")
    assert dirgha("a") == "A"


def test_guna_of_diphthongs_is_nearest_guna_vowel() -> None:
    assert [guna(c) for c in "eEoO"] == ["e", "e", "o", "o"]
