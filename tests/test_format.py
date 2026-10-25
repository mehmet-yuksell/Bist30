"""ui/format.py içindeki Türkçe sayı/tarih biçimlendirme işlevleri için testler."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.format import MINUS, arrow, direction, fmt_compact, fmt_date, fmt_num, fmt_pct, fmt_price


def test_fmt_num_uses_turkish_separators():
    assert fmt_num(1234.56) == "1.234,56"
    assert fmt_num(1234567.891, 1) == "1.234.567,9"
    assert fmt_num(0.5, 2) == "0,50"
    assert fmt_num(-1234.5) == f"{MINUS}1.234,50"


def test_fmt_num_rounding_to_zero_has_no_sign():
    assert fmt_num(-0.001, 2) == "0,00"


def test_fmt_num_missing_values():
    assert fmt_num(None) == "—"
    assert fmt_num(float("nan")) == "—"
    assert fmt_num(np.nan) == "—"


def test_fmt_pct_signed_format():
    assert fmt_pct(1.234) == "%+1,23"
    assert fmt_pct(-0.5) == f"%{MINUS}0,50"
    assert fmt_pct(0.0) == "%0,00"
    assert fmt_pct(42.3, 1, signed=False) == "%42,3"


def test_arrow_and_direction_follow_sign():
    assert (arrow(2.1), direction(2.1)) == ("▲", "up")
    assert (arrow(-0.3), direction(-0.3)) == ("▼", "down")
    assert (arrow(0.001), direction(0.001)) == ("•", "flat")
    assert direction(None) == "flat"


def test_fmt_compact_uses_turkish_suffixes():
    assert fmt_compact(46_611_644) == "46,6 Mn"
    assert fmt_compact(2_500_000_000) == "2,5 Mr"
    assert fmt_compact(12_300) == "12,3 Bin"
    assert fmt_compact(950) == "950"


def test_fmt_date_and_price():
    assert fmt_date(pd.Timestamp("2026-10-23")) == "23.10.2026"
    assert fmt_price(258, "TL") == "258,00 ₺"
    assert fmt_price(5.19, "USD") == "5,19 $"


def test_ui_text_has_no_buy_sell_language():
    import ui_text

    texts = [v for v in vars(ui_text).values() if isinstance(v, str)]
    texts += [v for v in ui_text.EXPLANATIONS.values()]
    for text in texts:
        upper = text.upper()
        assert "AL/SAT" not in upper
        assert " AL " not in f" {upper} " and " SAT " not in f" {upper} "
