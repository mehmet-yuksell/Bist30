"""backtest.py için testler: look-ahead olmaması, maliyet uygulanması, elle hesap."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backtest import Trade, _run_signal_strategy


def _make_df(opens: list[float]) -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=len(opens), freq="B")
    return pd.DataFrame({"Open": opens, "Close": opens}, index=dates)


def test_no_lookahead_entry_uses_next_day_open():
    # Sinyal gun1'in KAPANISINDA olusuyor (index 1); eger look-ahead olsaydi islem
    # index 1'in kendi Open'inda ya da Close'unda gerceklesirdi. Dogrusu: index 2'nin Open'i.
    opens = [100, 101, 999, 103, 104, 105]  # index2 Open'i bilerek carpici (999) yapildi
    df = _make_df(opens)

    enter = pd.Series([False, True, False, False, False, False], index=df.index)
    exit_ = pd.Series([False, False, False, False, False, False], index=df.index)

    result = _run_signal_strategy(df, enter, exit_, cost_pct=0.0, name="test")

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.entry_price == 999.0  # index2 Open'i -- sinyalin bir sonraki gunu
    assert trade.entry_date == df.index[2]


def test_no_lookahead_signal_on_last_day_has_no_effect():
    # Sinyal son gunun kapanisinda olussa bile, "ertesi gun" veri setinde yok -> islem olmaz.
    opens = [100, 101, 102, 103, 104, 105]
    df = _make_df(opens)

    enter = pd.Series([False, False, False, False, False, True], index=df.index)
    exit_ = pd.Series([False] * 6, index=df.index)

    result = _run_signal_strategy(df, enter, exit_, cost_pct=0.0, name="test")

    assert len(result.trades) == 0
    assert result.equity_curve.iloc[-1] == pytest.approx(100.0)


def test_cost_reduces_equity():
    opens = [100, 101, 102, 103, 104, 105]
    df = _make_df(opens)

    enter = pd.Series([False, True, False, False, False, False], index=df.index)
    exit_ = pd.Series([False, False, False, True, False, False], index=df.index)

    no_cost = _run_signal_strategy(df, enter, exit_, cost_pct=0.0, name="test")
    with_cost = _run_signal_strategy(df, enter, exit_, cost_pct=1.0, name="test")

    assert with_cost.equity_curve.iloc[-1] < no_cost.equity_curve.iloc[-1]


def test_hand_calculated_example():
    # index1 kapanisinda ENTER sinyali -> index2 Open'inda (102) girilir.
    # index3 kapanisinda EXIT sinyali -> index4 Open'inda (104) cikilir.
    opens = [100, 101, 102, 103, 104, 105]
    df = _make_df(opens)
    cost_pct = 1.0

    enter = pd.Series([False, True, False, False, False, False], index=df.index)
    exit_ = pd.Series([False, False, False, True, False, False], index=df.index)

    result = _run_signal_strategy(df, enter, exit_, cost_pct=cost_pct, name="test")

    # Giristen once (index 0, 1): pozisyon yok, equity tam 100 kalir.
    assert result.equity_curve.iloc[0] == pytest.approx(100.0)
    assert result.equity_curve.iloc[1] == pytest.approx(100.0)

    # Elle (teleskopik) hesap: ara gunlerdeki Open oranlari sadelesir,
    # sadece giris (102) ve cikis (104) fiyatlari ile iki yonlu maliyet kalir.
    cost_factor = 1 - cost_pct / 100
    expected_final = 100 * cost_factor * (104 / 102) * cost_factor

    assert result.equity_curve.iloc[-1] == pytest.approx(expected_final)
    assert result.total_return_pct == pytest.approx((expected_final / 100 - 1) * 100)

    # Cikistan sonra (index 5): pozisyon yok, equity sabit kalir.
    assert result.equity_curve.iloc[5] == pytest.approx(result.equity_curve.iloc[4])

    # Tek bir kapanmış işlem. Brüt getiri +%1.96 (102->104) ama iki yönlü %1 maliyet
    # (~%1.99 bileşik) bunu aşıyor, dolayısıyla net sonuç kayıp (win_rate %0) olmalı —
    # bu, maliyet modelinin gerçekten uygulandığının ayrı bir doğrulamasıdır.
    assert result.num_trades == 1
    assert result.win_rate_pct == pytest.approx(0.0)
    assert result.trades[0].entry_price == 102.0
    assert result.trades[0].exit_price == 104.0
    assert result.trades[0].net_return_pct(cost_pct) < 0


def test_open_position_at_end_is_not_counted_as_closed_trade():
    opens = [100, 101, 102, 103, 104, 105]
    df = _make_df(opens)

    enter = pd.Series([False, True, False, False, False, False], index=df.index)
    exit_ = pd.Series([False] * 6, index=df.index)  # hic exit sinyali yok

    result = _run_signal_strategy(df, enter, exit_, cost_pct=0.1, name="test")

    assert result.num_trades == 0  # acik islem "kapanmis" sayilmaz
    assert result.win_rate_pct is None
    assert len(result.trades) == 1
    assert result.trades[0].is_closed is False


def test_trade_net_return_pct():
    trade = Trade(pd.Timestamp("2026-01-01"), 100.0, pd.Timestamp("2026-01-05"), 110.0)

    # Maliyetsiz: %10 getiri
    assert trade.net_return_pct(0.0) == pytest.approx(10.0)

    # %1 maliyetle (iki yonlu, carpimsal): 0.99 * 1.10 * 0.99 - 1
    expected = (0.99 * 1.10 * 0.99 - 1) * 100
    assert trade.net_return_pct(1.0) == pytest.approx(expected)
