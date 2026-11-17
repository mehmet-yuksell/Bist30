"""docs/sistem_raporu.md'yi üretir: sinyal sisteminin geçmiş performans raporu.

Kullanım (proje kökünden):
    python tools/sistem_raporu.py            # önbellekteki veriyle
    python tools/sistem_raporu.py --yenile   # veriyi Yahoo'dan yeniden indir

Veri: BIST 100 hisseleri (bugünkü liste) + XU100, Yahoo Finance, 10 yıl (göstergeler 2021
başında oturmuş olsun diye). data.py'nin indirme fonksiyonları önbelleksiz (__wrapped__)
çağrılır; indirilen veri .eval_cache/ klasöründe saklanır (git'e girmez).
"""

import argparse
import sys
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

import evaluation as ev  # noqa: E402
import motor_veri  # noqa: E402
import tarayici_motor as motor  # noqa: E402
from config import BIST100_TICKERS, BIST100_LAST_UPDATED  # noqa: E402
from data import get_multiple_price_histories, get_price_history  # noqa: E402

CACHE = ROOT / ".eval_cache"
REPORT = ROOT / "docs" / "sistem_raporu.md"
PERIOD = "10y"
ILK_BAR_GUNLUK = motor_veri.MIN_BARS  # göstergelerin oturması için atlanan ilk günler
ILK_BAR_HAFTALIK = 52                 # orta vadede atlanan ilk haftalar

VADELER = {
    "kisa": {"ad": "Kısa vade (günlük)", "ayar": motor.KISA_VADE, "timeout": 20, "birim": "gün"},
    "orta": {"ad": "Orta vade (haftalık)", "ayar": motor.ORTA_VADE, "timeout": 12, "birim": "hafta"},
}
SATIS_SINYALLERI = {"SAT": "SAT", "KAR_AL": "KAR AL", "CIK": "ÇIK"}


# ---------------------------------------------------------------------------
# Veri
# ---------------------------------------------------------------------------

def veri_yukle(yenile: bool) -> tuple[dict, pd.DataFrame]:
    CACHE.mkdir(exist_ok=True)
    hisse_yolu, endeks_yolu = CACHE / "hisseler_10y.pkl", CACHE / "xu100.pkl"
    if yenile or not hisse_yolu.exists():
        hisseler = get_multiple_price_histories.__wrapped__(tuple(BIST100_TICKERS), period=PERIOD)
        pd.to_pickle(hisseler, hisse_yolu)
        endeks = get_price_history.__wrapped__("XU100", date(2015, 1, 1), date.today())
        pd.to_pickle(endeks, endeks_yolu)
    return pd.read_pickle(hisse_yolu), pd.read_pickle(endeks_yolu)


def haftalik_endeks(endeks: pd.DataFrame) -> pd.DataFrame:
    return motor.haftaliga_cevir(endeks[["Open", "High", "Low", "Close", "Volume"]])


# ---------------------------------------------------------------------------
# Sinyal üretimi ve işlemler
# ---------------------------------------------------------------------------

def vade_sonucu(girdi: pd.DataFrame, vade: str) -> tuple[pd.DataFrame, int]:
    """Motor sonucu ve atlanacak ilk bar sayısı. Orta vadede yarım hafta atılır."""
    ayar = VADELER[vade]["ayar"]
    if vade == "kisa":
        return motor.hisse_analiz(girdi, ayar), ILK_BAR_GUNLUK
    haftalik = ev.tamamlanmis_haftalar(motor.haftaliga_cevir(girdi), girdi.index[-1])
    return motor.sinyalleri_hesapla(haftalik, ayar), ILK_BAR_HAFTALIK


def satis_seviyeleri(sonuc: pd.DataFrame, ayar) -> tuple[pd.Series, pd.Series]:
    """Satış sinyalleri için alım seviyelerinin aynası: stop yukarıda, hedef aşağıda."""
    mesafe = sonuc["ATR"] * ayar.stop_atr
    return sonuc["Close"] + mesafe, sonuc["Close"] - mesafe * ayar.risk_odul


def tum_islemler(hisseler: dict, endeks: pd.DataFrame) -> dict[str, dict[str, pd.DataFrame]]:
    """{vade: {sinyal türü: işlemler}}; 'RASTGELE_AL' ve 'RASTGELE_SAT' her bardan giriştir."""
    endeksler = {"kisa": endeks, "orta": haftalik_endeks(endeks)}
    sonuc = {vade: {} for vade in VADELER}
    for vade, bilgi in VADELER.items():
        alim = ev.Kurallar(timeout=bilgi["timeout"], side=1)
        satis = ev.Kurallar(timeout=bilgi["timeout"], side=-1)
        parcalar: dict[str, list] = {}
        for kod, df in hisseler.items():
            girdi = motor_veri.motor_girdisi(df)
            if len(girdi) < motor_veri.MIN_BARS:
                continue
            s, ilk_bar = vade_sonucu(girdi, vade)
            herkes = pd.Series(True, index=s.index)
            s_stop, s_hedef = satis_seviyeleri(s, bilgi["ayar"])
            isler = {
                "AL": ev.islemler(s, s["AL"], s["Stop"], s["Hedef"], alim, kod, ilk_bar),
                "RASTGELE_AL": ev.islemler(s, herkes, s["Stop"], s["Hedef"], alim, kod, ilk_bar),
                "RASTGELE_SAT": ev.islemler(s, herkes, s_stop, s_hedef, satis, kod, ilk_bar),
            }
            for sutun in SATIS_SINYALLERI:
                isler[sutun] = ev.islemler(s, s[sutun], s_stop, s_hedef, satis, kod, ilk_bar)
            for tur, t in isler.items():
                parcalar.setdefault(tur, []).append(t)
        for tur, liste in parcalar.items():
            t = pd.concat([x for x in liste if not x.empty], ignore_index=True)
            t = t[t["tarih"] >= ev.GELISTIRME[0]].reset_index(drop=True)
            t["endeks"] = ev.endeks_getirisi(t, endeksler[vade])
            sonuc[vade][tur] = t
    return sonuc


# ---------------------------------------------------------------------------
# Rapor
# ---------------------------------------------------------------------------

def _f(x, nd=1, suffix=""):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return f"{x:.{nd}f}{suffix}".replace(".", ",")


def _gun(s: dict) -> str:
    if not np.isfinite(s.get("hedef_medyan_gun", np.nan)):
        return "—"
    return f"{s['hedef_medyan_gun']:.0f} ({s['hedef_gun_q1']:.0f}–{s['hedef_gun_q3']:.0f})"


BASLIK = ("| Sinyal | Sinyal sayısı | Hedef % | Stop % | Zaman aşımı % | Beklenen getiri (R) | "
          "Kâr faktörü | Ort. net getiri % | Hedefe medyan {birim} (Q1–Q3) | En uzun kayıp serisi | "
          "XU100 aynı tarihlerde % | XU100'e göre fark % |")
AYRAC = "|---|" + "---:|" * 11


def satir(ad: str, s: dict) -> str:
    if not s.get("sinyal"):
        return f"| {ad} | 0 |" + " — |" * 10
    return (
        f"| {ad} | {s['sinyal']} | {_f(s['hedef_pct'])} | {_f(s['stop_pct'])} | {_f(s['zaman_pct'])} | "
        f"**{_f(s['beklenen_r'], 3)}** | {_f(s['kar_faktoru'], 2)} | {_f(s['ort_getiri_pct'], 2)} | "
        f"{_gun(s)} | {s['kayip_serisi']} | {_f(s.get('endeks_ort_pct'), 2)} | "
        f"{_f(s.get('endeks_fazla_pct'), 2)} |"
    )


def vade_tablosu(isler: dict[str, pd.DataFrame], donem: str, birim: str) -> tuple[list[str], dict]:
    satirlar = [BASLIK.format(birim=birim), AYRAC]
    ozetler = {}
    sira = [("AL", "AL", 1), ("RASTGELE_AL", "Rastgele gün (alım, aynı kurallar)", 1)]
    sira += [(k, ad, -1) for k, ad in SATIS_SINYALLERI.items()]
    sira += [("RASTGELE_SAT", "Rastgele gün (satış, aynı kurallar)", -1)]
    for tur, ad, side in sira:
        s = ev.doneme_gore(isler[tur], side)[donem]
        ozetler[tur] = s
        satirlar.append(satir(ad, s))
    return satirlar, ozetler


def rapor_yaz(sonuc: dict, endeks: pd.DataFrame, hisse_sayisi: int, veri_bitis: pd.Timestamp) -> dict:
    out = [
        "# BIST Sinyal Sistemi Raporu",
        "",
        "> Eğitim amaçlıdır, yatırım tavsiyesi değildir. Geçmiş performans gelecek için garanti değildir.",
        "",
        f"Bu dosya `python tools/sistem_raporu.py` ile üretilir; elle düzenlemeyin. "
        f"Veri sonu: **{veri_bitis:%d.%m.%Y}**.",
        "",
        "## Metodoloji",
        "",
        f"- **Evren:** {hisse_sayisi} hisse, Borsa İstanbul'un {BIST100_LAST_UPDATED} tarihli BIST 100 listesi; "
        "Yahoo Finance günlük verisi, 10 yıl.",
        "- **Fiyat:** temettü düzeltmeli (Adj Close / Close) ve bölünme/bedelsiz onarımlı "
        "(`motor_veri.bolunme_onar`; açılış ±%10 limit dışındaysa kurumsal işlem sayılır).",
        "- **Dönemler (sinyal tarihine göre):** GELİŞTİRME 01.01.2021–31.12.2024, TEST 01.01.2025–bugün. "
        "Göstergeler daha eski veriyle ısınır; hissenin ilk 120 günü (orta vadede 52 haftası) sinyal olarak alınmaz.",
        "- **Giriş:** sinyal barının ertesi barının açılışı. **Stop / hedef:** sinyal barındaki motor seviyeleri "
        "(stop = kapanış − 1,5 ATR, hedef = kapanış + 3 ATR; orta vadede 2 ATR ve 4 ATR). "
        "Aynı barda hem stop hem hedef görülürse stop sayılır. Stop/hedefin ötesinde açılan barda çıkış açılıştan.",
        "- **Zaman aşımı:** kısa vadede 20 işlem günü, orta vadede 12 hafta (giriş barı dahil); son barın kapanışından çıkış.",
        "- **Satış sinyalleri (SAT, KAR AL, ÇIK)** açığa satış gibi değerlendirilir: stop = kapanış + 1,5 ATR, "
        "hedef = kapanış − 3 ATR. Soru: sinyalden sonra fiyat düştü mü?",
        "- **Maliyet:** her işleme gidiş-dönüş %0,2. **1R** = giriş ile stop arası mesafe; R getirileri maliyet sonrasıdır.",
        "- **Rastgele gün:** aynı hisselerde, aynı dönemde **her** bardan aynı kurallarla (aynı stop/hedef formülü, "
        "aynı zaman aşımı) giriş. Bir sinyal ancak bundan iyiyse bilgi taşır.",
        "- **XU100:** her işlem için endeksin aynı giriş-çıkış tarihlerindeki getirisi ve dönem boyunca al-tut getirisi.",
        "- **Açık** (zaman penceresi henüz dolmamış) ve **geçersiz** (giriş açılışı stop/hedefin ötesinde) işlemler "
        "metriklere girmez; sayıları tablonun altında.",
        "",
        "## Aşama 1 — Başlangıç ölçümü (filtresiz sistem)",
        "",
        "Bu bölüm kıyas noktasıdır: sonraki aşamalardaki filtreler bu rakamlara göre değerlendirilir.",
        "",
    ]
    tum_ozet = {}
    for vade, bilgi in VADELER.items():
        out += [f"### {bilgi['ad']}", ""]
        tum_ozet[vade] = {}
        for donem in ("TEST", "GELİŞTİRME"):
            bas, bit = ev.DONEMLER[donem]
            satirlar, ozetler = vade_tablosu(sonuc[vade], donem, bilgi["birim"])
            tum_ozet[vade][donem] = ozetler
            vurgu = " ⬅ asıl sonuç" if donem == "TEST" else ""
            out += [f"**{donem}**{vurgu} · XU100 al-tut: {_f(ev.al_tut(endeks, bas, bit) * 100, 1, '%')}", ""]
            out += satirlar
            acik = {k: (v.get("acik", 0), v.get("gecersiz", 0)) for k, v in ozetler.items()}
            out += ["", "Açık / geçersiz işlem sayısı: " + ", ".join(
                f"{k} {a}/{g}" for k, (a, g) in acik.items()), ""]
    out += ana_bulgular(tum_ozet)
    out += sinirlamalar()
    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")
    return tum_ozet


def ana_bulgular(tum_ozet: dict) -> list[str]:
    """Her sinyali aynı kurallarla rastgele girişe karşı iki dönemde kıyaslar."""
    out = ["### Ana bulgular (beklenen getiri, sinyal − rastgele gün)", "",
           "| Vade | Sinyal | GELİŞTİRME fark (R) | TEST fark (R) | Yorum |", "|---|---|---:|---:|---|"]
    for vade, bilgi in VADELER.items():
        for tur, ad in [("AL", "AL")] + list(SATIS_SINYALLERI.items()):
            rastgele = "RASTGELE_AL" if tur == "AL" else "RASTGELE_SAT"
            farklar = []
            for donem in ("GELİŞTİRME", "TEST"):
                s, b = tum_ozet[vade][donem][tur], tum_ozet[vade][donem][rastgele]
                farklar.append(s.get("beklenen_r", np.nan) - b.get("beklenen_r", np.nan))
            gel, test = farklar
            if gel > 0 and test > 0:
                yorum = "iki dönemde de rastgeleden iyi"
            elif gel > 0 >= test:
                yorum = "GELİŞTİRME'de iyi, TEST'te rastgeleden kötü"
            elif test > 0 >= gel:
                yorum = "yalnızca TEST'te rastgeleden iyi"
            else:
                yorum = "iki dönemde de rastgeleden kötü"
            out.append(f"| {bilgi['ad']} | {ad} | {_f(gel, 3)} | {_f(test, 3)} | {yorum} |")
    return out + [""]


def sinirlamalar() -> list[str]:
    return [
        "## Sınırlamalar",
        "",
        "- **Hayatta kalma yanlılığı:** test evreni bugünkü BIST 100 listesidir. Geçmişte endekste olup "
        "çıkarılan, iflas eden ya da işlemden kaldırılan hisseler yoktur; endekse sonradan girenler genelde iyi "
        "performans gösterdiği için girmiştir. Sonuçlar bu yüzden olduğundan iyi görünebilir.",
        "- Bazı hisseler borsaya 2021'den sonra girdi; GELİŞTİRME döneminde daha az hisse vardır.",
        "- Bölünme/bedelsiz onarımında oran açılış boşluğundan tahmin edilir; hata en fazla o geceki gerçek "
        "piyasa hareketi kadardır. Limit içinde kalan küçük bedelli/bedelsizler onarılmaz.",
        "- Gün içi fiyat sırası bilinmez: aynı barda stop ve hedef görüldüyse stop sayılır (kötümser).",
        "- Likidite, tavan/taban kilidinde işlem yapılamaması ve açığa satış kısıtları modellenmemiştir.",
        "- Rastgele gün kıyası her barı kullanır; ardışık günlerin işlemleri birbirinden bağımsız değildir.",
        "",
    ]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--yenile", action="store_true", help="veriyi Yahoo'dan yeniden indir")
    args = parser.parse_args()

    hisseler, endeks = veri_yukle(args.yenile)
    endeks.index = pd.DatetimeIndex(endeks.index).tz_localize(None) if endeks.index.tz else endeks.index
    sonuc = tum_islemler(hisseler, endeks)
    pd.to_pickle(sonuc, CACHE / "islemler.pkl")
    veri_bitis = max(df.index[-1] for df in hisseler.values())
    ozet = rapor_yaz(sonuc, endeks, len(hisseler), veri_bitis)
    for vade in ozet:
        for donem in ozet[vade]:
            s = ozet[vade][donem]
            print(vade, donem, {k: (v.get("sinyal"), _f(v.get("beklenen_r"), 3)) for k, v in s.items()})
    print("Yazıldı:", REPORT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
