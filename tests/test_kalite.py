"""kalite.py için testler."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import kalite as k


def test_score_bands():
    assert k.skor_araligi(59.9) is None
    assert k.skor_araligi(60) == "60-69"
    assert k.skor_araligi(79.99) == "70-79"
    assert k.skor_araligi(100) == "80+"
    assert k.grup_anahtari(85, True) == "80+ · filtre ✓"
    assert k.grup_anahtari(65, None) == "60-69"


def test_grades_follow_development_expectancy():
    assert k.not_ata({"60-69": 0.1, "70-79": 0.5, "80+": 0.3}) == {"70-79": "A", "80+": "B", "60-69": "C"}
    six = {f"g{i}": float(i) for i in range(6)}
    notlar = k.not_ata(six)
    assert [notlar[f"g{i}"] for i in (5, 4, 3, 2, 1, 0)] == ["A", "A", "B", "B", "C", "C"]
    assert k.not_ata({"x": np.nan}) == {}


def test_order_check():
    assert k.sira_tutuyor_mu({"A": 0.3, "B": 0.1, "C": -0.2})
    assert not k.sira_tutuyor_mu({"A": 0.1, "B": 0.3, "C": -0.2})
    assert k.sira_tutuyor_mu({"A": 0.3, "C": -0.2})  # B yoksa atlanır
    assert not k.sira_tutuyor_mu({"A": 0.3})


def test_lookup_hides_grade_when_not_validated():
    kal = {"kisa": {"gecerli": False, "filtreli": False,
                    "gruplar": {"70-79": {"not": "A", "hedef_pct": 40.0, "stop_pct": 50.0, "medyan_gun": 6.0, "sinyal": 100}}}}
    b = k.bilgi(kal, "kisa", 72)
    assert b["not"] is None and b["hedef_pct"] == 40.0
    kal["kisa"]["gecerli"] = True
    assert k.bilgi(kal, "kisa", 72)["not"] == "A"
    assert k.bilgi(kal, "kisa", 55) is None
    assert k.bilgi(kal, "orta", 72) is None


def test_lookup_uses_filter_on_filtered_horizon():
    kal = {"orta": {"gecerli": True, "filtreli": True,
                    "gruplar": {"80+ · filtre ✓": {"not": "A", "sinyal": 10},
                                "80+ · filtre ✗": {"not": "C", "sinyal": 5}}}}
    assert k.bilgi(kal, "orta", 90, filtre=True)["not"] == "A"
    assert k.bilgi(kal, "orta", 90, filtre=False)["not"] == "C"


def test_statistics():
    t = pd.DataFrame({"sonuc": ["hedef", "hedef", "stop", "zaman", "acik"],
                      "gun": [4, 8, 2, 20, np.nan], "r": [2.0, 2.0, -1.0, 0.5, 0.0]})
    s = k.istatistik(t)
    assert s["sinyal"] == 4
    assert s["hedef_pct"] == pytest.approx(50.0)
    assert s["stop_pct"] == pytest.approx(25.0)
    assert s["medyan_gun"] == pytest.approx(6.0)
    assert s["beklenen_r"] == pytest.approx(0.875)
