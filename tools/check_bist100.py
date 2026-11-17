"""config.BIST100_TICKERS listesini Borsa İstanbul'un güncel endeks bileşen dosyasıyla karşılaştırır.

Borsa İstanbul her işlem günü hangi hissenin hangi endekste olduğunu yayımlar:
https://www.borsaistanbul.com/datum/hisse_endeks_ds.csv (noktalı virgülle ayrılmış;
BIST 100 satırlarında ENDEKS KODU = XU100, bileşen kodu "THYAO.E" biçimindedir).

Kullanım (proje kökünden):
    python tools/check_bist100.py

Fark varsa eklenecek/çıkarılacak semboller yazdırılır ve çıkış kodu 1 olur; config.py elle
güncellenir (okunaklı şirket adları orada tutulduğu için dosya otomatik yazılmaz).
"""

import csv
import io
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import BIST100_TICKERS  # noqa: E402

SOURCE_URL = "https://www.borsaistanbul.com/datum/hisse_endeks_ds.csv"
INDEX_CODE = "XU100"


def fetch_constituents() -> tuple[dict[str, str], str]:
    response = requests.get(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    response.raise_for_status()
    rows = csv.reader(io.StringIO(response.content.decode("utf-8", errors="replace")), delimiter=";")
    constituents, as_of = {}, ""
    for row in rows:
        if len(row) >= 6 and row[2] == INDEX_CODE:
            constituents[row[0].removesuffix(".E")] = row[1]
            as_of = row[5]
    return constituents, as_of


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows konsolu varsayılan olarak cp1252
    official, as_of = fetch_constituents()
    if len(official) < 90:
        print(f"Beklenmeyen dosya içeriği: yalnızca {len(official)} XU100 satırı bulundu.")
        return 2

    added = sorted(set(official) - set(BIST100_TICKERS))
    removed = sorted(set(BIST100_TICKERS) - set(official))
    print(f"Borsa İstanbul XU100 ({as_of}): {len(official)} hisse; config: {len(BIST100_TICKERS)} hisse.")
    if not added and not removed:
        print("Liste güncel.")
        return 0
    for symbol in added:
        print(f"+ {symbol}  ({official[symbol]})")
    for symbol in removed:
        print(f"- {symbol}  ({BIST100_TICKERS[symbol]})")
    return 1


if __name__ == "__main__":
    sys.exit(main())
