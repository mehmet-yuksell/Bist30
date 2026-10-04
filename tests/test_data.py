"""data.py içindeki ağ gerektirmeyen (yerel dosya) işlevler için testler."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import BIST30_TICKERS
from data import load_all_bist_symbols


def test_load_all_bist_symbols_contains_known_tickers():
    symbols = load_all_bist_symbols()

    assert "THYAO" in symbols
    assert "akdolu" not in symbols  # saçma bir anahtar olmamalı
    assert "HAVA YOLLARI" in symbols["THYAO"].upper()

    assert "USAK" in symbols
    # Türkçe "İ" harfi .lower()/.upper() ile ASCII'ye güvenle dönüşmez
    # (örn. "İ".lower() -> "i̇", noktalı bileşik karakter); bu yüzden
    # kaynaktaki büyük harfli haliyle doğrudan karşılaştırıyoruz.
    assert "SERAMİK" in symbols["USAK"]


def test_load_all_bist_symbols_covers_bist30():
    symbols = load_all_bist_symbols()

    missing = [t for t in BIST30_TICKERS if t not in symbols]
    assert missing == []


def test_load_all_bist_symbols_no_empty_values():
    symbols = load_all_bist_symbols()

    assert len(symbols) > 500
    assert all(symbol.strip() for symbol in symbols)
    assert all(name.strip() for name in symbols.values())
