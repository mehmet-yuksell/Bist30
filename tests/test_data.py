"""data.py içindeki ağ gerektirmeyen (yerel dosya) işlevler için testler."""

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import data
from config import BIST30_TICKERS
from data import load_all_bist_symbols


def _ohlcv_with_missing_last_close() -> pd.DataFrame:
    """Yahoo'nun 30.10.2026'da döndürdüğü biçim: son günde Close NaN, diğerleri dolu."""
    idx = pd.to_datetime(["2026-10-27", "2026-10-28", "2026-10-30"])
    return pd.DataFrame(
        {
            "Open": [257.5, 252.5, 251.0],
            "High": [258.0, 254.5, 252.5],
            "Low": [252.75, 250.25, 242.2],
            "Close": [253.0, 252.5, np.nan],
            "Volume": [39168021, 8696283, 36919119],
        },
        index=idx,
    )


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


def test_price_history_drops_rows_without_close(monkeypatch):
    monkeypatch.setattr(data.yf, "download", lambda *a, **k: _ohlcv_with_missing_last_close())
    data.get_price_history.clear()

    df = data.get_price_history("THYAO", date(2026, 10, 27), date(2026, 10, 30))

    assert df.index[-1] == pd.Timestamp("2026-10-28")
    assert df["Close"].notna().all()


def test_multiple_histories_drop_rows_without_close(monkeypatch):
    raw = pd.concat({"THYAO.IS": _ohlcv_with_missing_last_close()}, axis=1)
    monkeypatch.setattr(data.yf, "download", lambda *a, **k: raw)
    data.get_multiple_price_histories.clear()

    result = data.get_multiple_price_histories(("THYAO",))

    assert result["THYAO"].index[-1] == pd.Timestamp("2026-10-28")
    assert result["THYAO"]["Close"].notna().all()
