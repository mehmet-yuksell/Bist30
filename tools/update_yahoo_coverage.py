"""data/bist_all.csv'deki her sembol için Yahoo Finance'te güncel veri olup olmadığını işaretler.

KAP listesindeki şirketlerin bir kısmı (faktoring, varlık kiralama, fon şirketleri vb.)
borsada işlem görmez ve Yahoo'da verisi yoktur. Uygulamanın arama listeleri yalnızca
`yahoo_data` sütunu "1" olan sembolleri gösterir; böylece seçilen her hisse sonuç verir.

Kullanım (proje kökünden):
    python tools/update_yahoo_coverage.py

Liste değiştiğinde (yeni halka arz, işlemden kaldırma) yeniden çalıştırın.
"""

import csv
import logging
import sys
import warnings
from datetime import date
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import YAHOO_SUFFIX  # noqa: E402
from data import BIST_ALL_CSV_PATH  # noqa: E402

PERIOD = "3mo"
MIN_CLOSES = 20      # son 3 ayda en az bu kadar kapanış (göstergeler için anlamlı veri)
MAX_STALE_DAYS = 14  # en güncel kapanıştan bu kadar gün eski olan sembol işlem görmüyor sayılır
CHUNK = 100
MIN_COVERAGE = 0.5   # bunun altı muhtemelen ağ/hız sınırı sorunudur; dosyaya yazılmaz


def last_closes(symbols: list[str]) -> dict[str, pd.Series]:
    result = {}
    for i in range(0, len(symbols), CHUNK):
        chunk = symbols[i:i + CHUNK]
        raw = yf.download(
            [s + YAHOO_SUFFIX for s in chunk],
            period=PERIOD,
            group_by="ticker",
            auto_adjust=False,
            progress=False,
        )
        for symbol in chunk:
            try:
                result[symbol] = raw[symbol + YAHOO_SUFFIX]["Close"].dropna()
            except KeyError:
                result[symbol] = pd.Series(dtype=float)
        print(f"{i + len(chunk)}/{len(symbols)}")
    return result


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows konsolunda Türkçe çıktı
    warnings.filterwarnings("ignore")
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)

    with open(BIST_ALL_CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    closes = last_closes([row["symbol"] for row in rows])
    newest = max(c.index[-1] for c in closes.values() if len(c))

    def has_data(c: pd.Series) -> bool:
        return len(c) >= MIN_CLOSES and (newest - c.index[-1]).days <= MAX_STALE_DAYS

    flags = {symbol: has_data(c) for symbol, c in closes.items()}
    covered = sum(flags.values())
    if covered < MIN_COVERAGE * len(rows):
        print(f"Yalnızca {covered}/{len(rows)} sembolde veri var; dosya değiştirilmedi.")
        return 1

    today = date.today().isoformat()
    for row in rows:
        row["yahoo_data"] = "1" if flags[row["symbol"]] else "0"
        row["yahoo_checked"] = today

    fields = ["symbol", "company_name", "source", "updated_date", "yahoo_data", "yahoo_checked"]
    with open(BIST_ALL_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"{covered}/{len(rows)} sembolde güncel veri var (en güncel kapanış {newest.date()}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
