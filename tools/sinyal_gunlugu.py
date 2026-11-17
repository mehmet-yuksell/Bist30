"""Günün sinyallerini data/sinyal_gunlugu.csv'ye ekler (İleri Test için).

Kullanım (proje kökünden, kapanıştan sonra):
    python tools/sinyal_gunlugu.py

GitHub Actions (.github/workflows/sinyal_gunlugu.yml) her iş günü 18:45'te (Türkiye) çalıştırır ve
dosya değiştiyse commit eder. Bugünün (Europe/Istanbul) kapanış verisi yoksa (tatil, hafta sonu,
Yahoo henüz güncellemediyse) hiçbir şey yazmaz. Aynı gün iki kez çalışırsa satırlar tekrarlanmaz.
Veri data.py'nin toplu indirmesiyle (önbelleksiz) alınır; data.py değişmez.
"""

import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

import gunluk  # noqa: E402
import kalite  # noqa: E402
import market  # noqa: E402
import panel_veri as pv  # noqa: E402
from config import BIST100_TICKERS  # noqa: E402
from data import get_multiple_price_histories  # noqa: E402

DOSYA = ROOT / "data" / "sinyal_gunlugu.csv"
ENDEKS = "XU100"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    bugun = market.now().date()
    if bugun.weekday() >= 5:
        print(f"{bugun}: hafta sonu, kayıt yok.")
        return 0
    kodlar = tuple(BIST100_TICKERS)
    histories = get_multiple_price_histories.__wrapped__(kodlar + (ENDEKS,))
    kalibrasyon = kalite.yukle()

    def not_bul(skor: float, vade: str) -> str | None:
        bilgi = kalite.bilgi(kalibrasyon, vade, skor, True if vade == pv.ORTA else None)
        return bilgi.get("not") if bilgi else None

    yeni = gunluk.gunun_sinyalleri(histories, histories.get(ENDEKS), bugun, kodlar, not_bul)
    eski = gunluk.oku(DOSYA)
    guncel = gunluk.ekle(eski, yeni)
    eklenen = len(guncel) - len(eski)
    bugun_verisi = sum(1 for k in kodlar if k in histories and histories[k].index[-1].date() == bugun)
    print(f"{bugun}: bugünün verisi olan hisse {bugun_verisi}/{len(kodlar)}, yeni sinyal {eklenen}, "
          f"günlükte toplam {len(guncel)}.")
    if eklenen or not DOSYA.exists():
        DOSYA.parent.mkdir(exist_ok=True)
        guncel.to_csv(DOSYA, index=False, float_format="%.4f")
    return 0


if __name__ == "__main__":
    sys.exit(main())
