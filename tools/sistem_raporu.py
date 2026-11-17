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
from dataclasses import replace
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

import evaluation as ev  # noqa: E402
import filtreler  # noqa: E402
import firsat  # noqa: E402
import kalite  # noqa: E402
import portfoy  # noqa: E402
import motor_veri  # noqa: E402
import tarayici_motor as motor  # noqa: E402
from config import BIST100_TICKERS, BIST100_LAST_UPDATED  # noqa: E402
from data import get_multiple_price_histories, get_price_history  # noqa: E402

CACHE = ROOT / ".eval_cache"
REPORT = ROOT / "docs" / "sistem_raporu.md"
# Panelin "Sistem Performansı" sekmesi bu dosyaları okur (git'e girer)
PERFORMANS_CSV = ROOT / "data" / "sistem_performansi.csv"
PERFORMANS_JSON = ROOT / "data" / "sistem_performansi.json"
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


def filtre_bayraklari(girdi: pd.DataFrame, s: pd.DataFrame, endeks: pd.DataFrame) -> dict[str, pd.Series]:
    """Sinyal barları için her filtre varyantının geçip geçmediği ('F1|EMA 50' gibi anahtarlar)."""
    oz = filtreler.zaman_dilimine_hizala(filtreler.gunluk_ozellikler(girdi, endeks), s.index)
    bayrak = {}
    for f, (_, varyantlar) in filtreler.FILTRELER.items():
        if f == "F7":
            continue
        for etiket, esik in varyantlar.items():
            bayrak[f"{f}|{etiket}"] = filtreler.maske(f, esik, oz, s)
    return bayrak


def _bayrak_ekle(t: pd.DataFrame, bayrak: dict[str, pd.Series]) -> pd.DataFrame:
    if t.empty:
        return t
    for anahtar, seri in bayrak.items():
        t[anahtar] = seri.reindex(t["tarih"]).to_numpy(dtype=bool)
    return t


FIRSAT_ETIKET = ["K1", "K2", "K3", "K4", "uyari_hisseye_ozel", "uyari_piyasa"]
# Eleme ayırmazsa denenecek eşikler (kriter başına en fazla 3; ortadaki asıl tanım)
K_VARYANT = {
    "K1": {"2/3 gün": {"k1_gun": 2, "k1_pencere": 3}, "3/3 gün": {"k1_gun": 3, "k1_pencere": 3},
           "4/5 gün": {"k1_gun": 4, "k1_pencere": 5}},
    "K2": {"2× hacim": {"hacim_kat": 2.0}, "3× hacim": {"hacim_kat": 3.0}, "4× hacim": {"hacim_kat": 4.0}},
    "K3": {"26 hafta": {"yil_gun": 126}, "52 hafta": {"yil_gun": 252}, "104 hafta": {"yil_gun": 504}},
    "K4": {"çarpan 2": {"k4_carpan": 2.0}, "çarpan 3": {"k4_carpan": 3.0}, "çarpan 4": {"k4_carpan": 4.0}},
}


def firsat_islemleri(girdi: pd.DataFrame, endeks: pd.DataFrame, kod: str) -> dict[str, pd.DataFrame]:
    """FIRSAT sistemi işlemleri ve kıyasları; ayrıca düşüş bölümlerinin 20 günlük getirisi."""
    s = firsat.firsat_hesapla(girdi, endeks)
    ilk = ILK_BAR_GUNLUK

    def etiketle(t: pd.DataFrame) -> pd.DataFrame:
        if not t.empty:
            for col in FIRSAT_ETIKET:
                t[col] = s[col].reindex(t["tarih"]).to_numpy(dtype=bool)
        return t

    # Her kriter eşiği için bayraklar (tetik ve bölüm başı kriterlerden bağımsızdır)
    varyant_bayrak = {}
    for key, varyantlar in K_VARYANT.items():
        for etiket, ayar in varyantlar.items():
            sv = firsat.firsat_hesapla(girdi, endeks, replace(firsat.VARSAYILAN, **ayar))
            varyant_bayrak[f"{key}|{etiket}"] = sv[key]

    def etiketle_varyant(t: pd.DataFrame) -> pd.DataFrame:
        if not t.empty:
            for anahtar, seri in varyant_bayrak.items():
                t[anahtar] = seri.reindex(t["tarih"]).to_numpy(dtype=bool)
        return t

    def oncelikli(t: pd.DataFrame) -> pd.DataFrame:
        if not t.empty:  # portföyde sıralama: RSI(2) düşük olan önce
            t["oncelik"] = 100 - s["RSI2"].reindex(t["tarih"]).to_numpy()
        return t

    sonuc = {
        "F_FIRSAT": oncelikli(etiketle(firsat.islemler(s, s["FIRSAT"], kod, ilk))),
        "F_BICAK": etiketle(firsat.islemler(s, s["BICAK"], kod, ilk)),
        "F_TETIK": etiketle_varyant(etiketle(firsat.islemler(s, s["tetik"], kod, ilk))),
        "F_KURULUM": firsat.islemler(s, s["bolum_basi"], kod, ilk),
        "F_RASTGELE": firsat.islemler(s, pd.Series(True, index=s.index), kod, ilk),
    }
    # Düşüş bölümleri: bölüm başında (o güne kadarki bilgiyle) bıçak riski var mı, 20 gün sonra ne oldu
    o, c = s["Open"].to_numpy(), s["Close"].to_numpy()
    satirlar = []
    for i in np.flatnonzero(s["bolum_basi"].to_numpy()):
        if i < ilk or i + 20 >= len(s):
            continue
        satirlar.append({
            "kod": kod, "tarih": s.index[i], "giris_tarihi": s.index[i + 1], "cikis_tarihi": s.index[i + 20],
            "getiri20": c[i + 20] / o[i + 1] - 1,
            "bicak": bool(s["BICAK_RISKI"].iloc[i]),
            **{key: bool(s[key].iloc[i]) for key in firsat.BICAK_KRITERLERI},
            **{anahtar: bool(seri.iloc[i]) for anahtar, seri in varyant_bayrak.items()},
        })
    sonuc["F_BOLUM"] = pd.DataFrame(satirlar)
    return sonuc


def tum_islemler(hisseler: dict, endeks: pd.DataFrame) -> dict[str, dict[str, pd.DataFrame]]:
    """{vade: {sinyal türü: işlemler}}; 'RASTGELE_AL' ve 'RASTGELE_SAT' her bardan giriştir.

    AL işlemlerine filtre bayrakları eklenir; 'AL_F7|<varyant>' teyitli ve bir bar gecikmeli
    girişlerdir (Aşama 2).
    """
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
            bayrak = filtre_bayraklari(girdi, s, endeks)
            isler = {
                "AL": _bayrak_ekle(ev.islemler(s, s["AL"], s["Stop"], s["Hedef"], alim, kod, ilk_bar), bayrak),
                "RASTGELE_AL": ev.islemler(s, herkes, s["Stop"], s["Hedef"], alim, kod, ilk_bar),
                "RASTGELE_SAT": ev.islemler(s, herkes, s_stop, s_hedef, satis, kod, ilk_bar),
            }
            if not isler["AL"].empty:
                isler["AL"]["oncelik"] = s["Alim_skor"].reindex(isler["AL"]["tarih"]).to_numpy()
            for etiket, seviye in filtreler.FILTRELER["F7"][1].items():
                teyitli = s["AL"] & filtreler.teyit(s, seviye)
                isler[f"AL_F7|{etiket}"] = _bayrak_ekle(
                    ev.islemler_gecikmeli(s, teyitli, s["Stop"], s["Hedef"], alim, kod, ilk_bar), bayrak)
                isler[f"AL_F7_ANINDA|{etiket}"] = ev.islemler(s, teyitli, s["Stop"], s["Hedef"], alim, kod, ilk_bar)
            for sutun in SATIS_SINYALLERI:
                isler[sutun] = ev.islemler(s, s[sutun], s_stop, s_hedef, satis, kod, ilk_bar)
            if vade == "kisa":
                isler.update(firsat_islemleri(girdi, endeks, kod))
            for tur, t in isler.items():
                parcalar.setdefault(tur, []).append(t)
        for tur, liste in parcalar.items():
            dolu = [x for x in liste if not x.empty]
            if not dolu:
                sonuc[vade][tur] = pd.DataFrame(columns=["kod", "tarih", "sonuc"])
                continue
            t = pd.concat(dolu, ignore_index=True)
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


def rapor_yaz(sonuc: dict, endeks: pd.DataFrame, hisseler: dict, veri_bitis: pd.Timestamp) -> dict:
    hisse_sayisi = len(hisseler)
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
    asama2_satirlari, kabuller = asama2(sonuc)
    out += asama2_satirlari
    tum_ozet["kabuller"] = kabuller
    asama3_satirlari, firsat_karar = asama3(sonuc)
    out += asama3_satirlari
    tum_ozet["firsat"] = firsat_karar
    asama4_satirlari, kalite_ozet = asama4(sonuc, kabuller)
    out += asama4_satirlari
    tum_ozet["kalite"] = kalite_ozet
    asama3d_satirlari, portfoy_ozet = asama3d(sonuc, hisseler, endeks, kalite_ozet)
    out += asama3d_satirlari
    tum_ozet["portfoy"] = portfoy_ozet
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


# ---------------------------------------------------------------------------
# Aşama 2 — alım filtreleri
# ---------------------------------------------------------------------------

GEL_YILLARI = (2021, 2022, 2023, 2024)
MIN_TEST_SINYAL = 30


def _r(t: pd.DataFrame, donem: str) -> dict:
    return ev.doneme_gore(t)[donem]


def _yillik_r(t: pd.DataFrame) -> dict[int, float]:
    if t.empty:
        return {y: np.nan for y in GEL_YILLARI}
    return {y: ev.ozet(t[t["tarih"].dt.year == y]).get("beklenen_r", np.nan) for y in GEL_YILLARI}


def filtreli(sonuc_vade: dict, f: str, etiket: str) -> pd.DataFrame:
    if f == "F7":
        return sonuc_vade[f"AL_F7|{etiket}"]
    base = sonuc_vade["AL"]
    return base[base[f"{f}|{etiket}"]]


def birlesik(sonuc_vade: dict, kabul: dict[str, str]) -> pd.DataFrame:
    """Kabul edilen filtrelerin hepsi (F7 kabul edildiyse gecikmeli girişle)."""
    t = sonuc_vade[f"AL_F7|{kabul['F7']}"] if "F7" in kabul else sonuc_vade["AL"]
    for f, etiket in kabul.items():
        if f != "F7":
            t = t[t[f"{f}|{etiket}"]]
    return t


def asama2(sonuc: dict) -> tuple[list[str], dict]:
    out = [
        "## Aşama 2 — Alım sinyali kalite filtreleri",
        "",
        "Her filtre başlangıç sistemine **tek başına** eklendi. Eşik seçimi yalnızca GELİŞTİRME verisiyle yapıldı: "
        "her eşik için 2021, 2022, 2023 ve 2024 yıllarında beklenen getirinin başlangıca göre farkı hesaplandı; "
        "**en çok yılda iyileştiren** eşik seçildi (eşitlikte en kötü yıldaki fark büyük olan). TEST sonucuna yalnızca "
        "seçilen eşik için, kabul kararı aşamasında bakıldı; seçilmeyen eşiklerin TEST sonucu bu yüzden tabloda yok.",
        "",
        "Kabul şartları (üçü birlikte): (a) TEST'te beklenen getiriyi artırır, (b) GELİŞTİRME'de de artırır, "
        f"(c) TEST'te en az {MIN_TEST_SINYAL} sinyal bırakır.",
        "",
        "> **Çoklu deneme uyarısı:** 8 filtre × 2 vade denendi. Bunlardan bazıları yalnızca şans eseri iki dönemde de "
        "olumlu çıkabilir. Kabul edilen bir filtre \"kanıtlanmış iyileşme\" değil, bu kurallardan geçmiş bir adaydır.",
        "",
    ]
    kabuller = {}
    for vade, bilgi in VADELER.items():
        sv = sonuc[vade]
        base = sv["AL"]
        base_gel, base_test = _r(base, "GELİŞTİRME"), _r(base, "TEST")
        base_yil = _yillik_r(base)
        out += [f"### {bilgi['ad']}", "",
                f"Başlangıç: GELİŞTİRME {base_gel['sinyal']} sinyal, {_f(base_gel['beklenen_r'], 3)} R "
                f"(standart hata ±{_f(base_gel['r_std_hata'], 3)}) · TEST {base_test['sinyal']} sinyal, "
                f"{_f(base_test['beklenen_r'], 3)} R (standart hata ±{_f(base_test['r_std_hata'], 3)}). "
                "Standart hatadan küçük farklar gürültüden ayırt edilemez.", "",
                "**Eşik seçimi (yalnızca GELİŞTİRME)**", "",
                "| Filtre | Eşik | Sinyal | Beklenen R | Fark (R) | İyileşen yıl | En kötü yıl farkı | Seçildi |",
                "|---|---|---:|---:|---:|---:|---:|:---:|"]
        secim = {}
        for f, (aciklama, varyantlar) in filtreler.FILTRELER.items():
            adaylar = []
            for etiket in varyantlar:
                t = filtreli(sv, f, etiket)
                gel = _r(t, "GELİŞTİRME")
                yil = _yillik_r(t)
                fark = {y: yil[y] - base_yil[y] for y in GEL_YILLARI}
                adaylar.append((filtreler.yillik_tutarlilik(fark), etiket, gel))
            en_iyi = max(adaylar, key=lambda a: a[0])
            secim[f] = en_iyi[1]
            for (iyi_yil, en_kotu), etiket, gel in adaylar:
                out.append(
                    f"| {f} | {etiket} | {gel.get('sinyal', 0)} | {_f(gel.get('beklenen_r'), 3)} | "
                    f"{_f(gel.get('beklenen_r', np.nan) - base_gel['beklenen_r'], 3)} | {iyi_yil}/4 | "
                    f"{_f(en_kotu, 3)} | {'✔' if etiket == en_iyi[1] else ''} |")
        out += ["", "**Kabul kararı**", "",
                "| Filtre | Tanım | Seçilen eşik | GEL fark (R) | TEST fark (R) | TEST sinyal | Karar | Gerekçe |",
                "|---|---|---|---:|---:|---:|---|---|"]
        kabul = {}
        for f, etiket in secim.items():
            t = filtreli(sv, f, etiket)
            gel, test = _r(t, "GELİŞTİRME"), _r(t, "TEST")
            d_gel = gel.get("beklenen_r", np.nan) - base_gel["beklenen_r"]
            d_test = test.get("beklenen_r", np.nan) - base_test["beklenen_r"]
            nedenler = []
            if not d_test > 0:
                nedenler.append("TEST'te beklenen getiriyi artırmıyor")
            if not d_gel > 0:
                nedenler.append("GELİŞTİRME'de artırmıyor")
            if test.get("sinyal", 0) < MIN_TEST_SINYAL:
                nedenler.append(f"TEST'te {test.get('sinyal', 0)} sinyal kalıyor (<{MIN_TEST_SINYAL})")
            if not nedenler:
                kabul[f] = etiket
            out.append(
                f"| {f} | {filtreler.FILTRELER[f][0]} | {etiket} | {_f(d_gel, 3)} | {_f(d_test, 3)} | "
                f"{test.get('sinyal', 0)} | {'**Kabul**' if not nedenler else 'Red'} | "
                f"{'; '.join(nedenler) if nedenler else 'üç şart da sağlandı'} |")
        kabuller[vade] = kabul

        # Önce / sonra tabloları
        satirlar = [("Başlangıç (filtresiz)", base)]
        satirlar += [(f"{f} ({secim[f]}){' ✔' if f in kabul else ''}", filtreli(sv, f, secim[f]))
                     for f in filtreler.FILTRELER]
        if kabul:
            satirlar.append(("Kabul edilenlerin hepsi birlikte: " + ", ".join(kabul), birlesik(sv, kabul)))
        for donem in ("TEST", "GELİŞTİRME"):
            out += ["", f"**Önce / sonra — {donem}**{' ⬅ asıl sonuç' if donem == 'TEST' else ''}", "",
                    BASLIK.format(birim=bilgi["birim"]), AYRAC]
            out += [satir(ad, _r(t, donem)) for ad, t in satirlar]

        # F7 gecikme maliyeti
        out += ["", "**F7 teyit gününün gecikme maliyeti** (aynı teyitli sinyaller: ertesi gün girişe karşı "
                "bir gün bekleyip giriş)", "",
                "> \"Hemen giriş\" gerçekte yapılamaz: teyit ertesi günün kapanışında bilinir, o güne girmek "
                "geleceği bilmek olur. Bu sütun yalnızca gecikmenin maliyetini ölçmek için vardır; F7'nin "
                "kendi sonucu \"gecikmeli giriş\"tir.", "",
                "| Teyit seviyesi | Dönem | Sinyal | Hemen giriş R | Gecikmeli giriş R | Gecikmenin etkisi (R) |",
                "|---|---|---:|---:|---:|---:|"]
        for etiket in filtreler.FILTRELER["F7"][1]:
            for donem in ("GELİŞTİRME", "TEST"):
                hemen = _r(sv[f"AL_F7_ANINDA|{etiket}"], donem)
                gec = _r(sv[f"AL_F7|{etiket}"], donem)
                out.append(f"| {etiket} | {donem} | {gec.get('sinyal', 0)} | {_f(hemen.get('beklenen_r'), 3)} | "
                           f"{_f(gec.get('beklenen_r'), 3)} | "
                           f"{_f(gec.get('beklenen_r', np.nan) - hemen.get('beklenen_r', np.nan), 3)} |")

        if kabul:
            t = birlesik(sv, kabul)
            gel, test = _r(t, "GELİŞTİRME"), _r(t, "TEST")
            d_gel = gel.get("beklenen_r", np.nan) - base_gel["beklenen_r"]
            d_test = test.get("beklenen_r", np.nan) - base_test["beklenen_r"]
            gecti = d_gel > 0 and d_test > 0 and test.get("sinyal", 0) >= MIN_TEST_SINYAL
            out += ["", f"**Birleşik sonuç:** {', '.join(f'{k} ({v})' for k, v in kabul.items())} birlikte · "
                    f"GELİŞTİRME farkı {_f(d_gel, 3)} R, TEST farkı {_f(d_test, 3)} R, TEST'te {test.get('sinyal', 0)} "
                    f"sinyal → {'üç şartı sağlıyor' if gecti else 'üç şartı birlikte sağlamıyor'}."]
        else:
            out += ["", "**Birleşik sonuç:** bu vadede kabul edilen filtre yok."]
        out.append("")
    out += ["### Motordaki karşılığı", "",
            "Kabul edilen filtreler `tarayici_motor.py`'de `AlimFiltreleri` ayarıyla açılıp kapatılabilir; skor ve "
            "`AL` sütunu değişmez, filtrelenmiş sinyal `AL_filtreli` sütunundadır.", ""]
    for vade, bilgi in VADELER.items():
        f = bilgi["ayar"].filtreler
        out.append(f"- {bilgi['ad']}: " + (
            f"aktif · piyasa_ema={f.piyasa_ema}, uzun_trend_ema={f.uzun_trend_ema}, tavan_esik={f.tavan_esik}"
            if f.aktif else "filtre yok"))
    out.append("")
    return out, kabuller


# ---------------------------------------------------------------------------
# Aşama 3 — FIRSAT sistemi
# ---------------------------------------------------------------------------

def _donem(t: pd.DataFrame, donem: str) -> pd.DataFrame:
    if t.empty:
        return t
    bas, bit = ev.DONEMLER[donem]
    return t[(t["tarih"] >= bas) & (t["tarih"] <= bit)]


def asama3(sonuc: dict) -> tuple[list[str], dict]:
    sv = sonuc["kisa"]
    out = [
        "## Aşama 3 — FIRSAT sistemi (sert düşüş sonrası toparlanma)",
        "",
        "Trend takip sisteminden bağımsız bir kural seti; yalnızca kısa vade (günlük). Kuralların tam metni "
        "`firsat.py` dosyasının başında. Tanımda açık olmayan üç nokta şöyle yorumlandı:",
        "",
        "- **Düşüş öncesi sağlamlık:** 1-5 günlük düşüş penceresinin başladığı günün kapanışı 200 günlük EMA'nın "
        "üstünde. Haftalık trend: tamamlanmış son haftalık kapanış 30 haftalık EMA'nın üstünde.",
        "- **Düşen bıçak elemesi:** düşüş bölümünün başından tetik gününe kadar herhangi bir gün bir kriter "
        "görüldüyse tetik elenir. K2'deki \"düşüş günleri\" son 5 gün; hacim ortalaması o günü içermeyen önceki "
        "20 gün. K4: tamamlanmış haftaların Supertrend'i (10, 3) aşağı yönde.",
        "- **Stop ve hedef:** stop, dönüş günü dahil son 10 günün en düşüğünün 0,5 ATR altı. Hedef her gün "
        "bir önceki günün 20 günlük EMA'sı ile giriş + 2R'nin küçüğü; giriş EMA'nın üstündeyse işlem açılmaz.",
        "",
    ]
    tumu = pd.concat([sv["F_FIRSAT"], sv["F_BICAK"]], ignore_index=True) if not sv["F_BICAK"].empty else sv["F_FIRSAT"]
    for donem in ("TEST", "GELİŞTİRME"):
        bas, bit = ev.DONEMLER[donem]
        out += [f"**{donem}**{' ⬅ asıl sonuç' if donem == 'TEST' else ''}", "",
                BASLIK.format(birim="gün"), AYRAC]
        for ad, tur in (("FIRSAT (eleme sonrası)", "F_FIRSAT"),
                        ("Elenen tetikler (düşen bıçak riski)", "F_BICAK"),
                        ("Tüm tetikler (eleme olmadan)", "F_TETIK"),
                        ("Kurulum günü giriş (dönüş beklenmeden)", "F_KURULUM"),
                        ("Rastgele gün (aynı stop/hedef/süre kuralları)", "F_RASTGELE")):
            out.append(satir(ad, _r(sv[tur], donem)))
        out.append("")

    # Kazanç / kayıp yapısı: yüksek hedef oranına rağmen neden negatif?
    out += ["**Kazanç / kayıp yapısı (FIRSAT)** — sonuç türüne göre ortalama R ve ortalama risk mesafesi", "",
            "| Dönem | Hedef: ort. R | Stop: ort. R | Zaman aşımı: ort. R | Ort. risk (giriş−stop, %) |",
            "|---|---:|---:|---:|---:|"]
    for donem in ("GELİŞTİRME", "TEST"):
        t = _donem(sv["F_FIRSAT"], donem)
        t = t[t["sonuc"].isin(ev.OUTCOMES)] if not t.empty else t
        if t.empty:
            continue
        ort = {s: t.loc[t["sonuc"] == s, "r"].mean() for s in ev.OUTCOMES}
        risk = ((t["giris"] - t["stop"]) / t["giris"]).mean() * 100
        out.append(f"| {donem} | {_f(ort['hedef'], 2)} | {_f(ort['stop'], 2)} | {_f(ort['zaman'], 2)} | {_f(risk, 1)} |")
    out.append("")

    # Kriter bazında
    out += ["**Düşen bıçak kriterleri tek tek** (tetiklerde; kriter görülen tetiklerin beklenen getirisi, "
            "kriter görülmeyen tetiklere göre)", "",
            "| Kriter | Dönem | Görülen tetik | Beklenen R (görülen) | Görülmeyen tetik | Beklenen R (görülmeyen) | Fark (R) |",
            "|---|---|---:|---:|---:|---:|---:|"]
    tetik = sv["F_TETIK"]
    for key, aciklama in firsat.BICAK_KRITERLERI.items():
        for donem in ("GELİŞTİRME", "TEST"):
            if tetik.empty:
                continue
            var, yok = _r(tetik[tetik[key]], donem), _r(tetik[~tetik[key]], donem)
            out.append(f"| {key} ({aciklama}) | {donem} | {var.get('sinyal', 0)} | {_f(var.get('beklenen_r'), 3)} | "
                       f"{yok.get('sinyal', 0)} | {_f(yok.get('beklenen_r'), 3)} | "
                       f"{_f(var.get('beklenen_r', np.nan) - yok.get('beklenen_r', np.nan), 3)} |")

    # Bölüm başı 20 günlük getiri
    bolum = sv["F_BOLUM"]
    out += ["", "**Düşüş bölümlerinin sonraki 20 günü** (bölümün ilk günü, o güne kadarki bilgiyle \"düşen bıçak "
            "riski\" var mı; ertesi gün açılıştan 20 gün sonraki kapanışa getiri, maliyetsiz)", "",
            "| Grup | Dönem | Bölüm sayısı | Ort. 20 gün getiri % | Medyan % | Negatif biten % | XU100 aynı tarihlerde % | XU100'e göre fark % |",
            "|---|---|---:|---:|---:|---:|---:|---:|"]
    ayrim = {}
    for donem in ("GELİŞTİRME", "TEST"):
        b = _donem(bolum, donem)
        for ad, grup in (("Düşen bıçak riski", b[b["bicak"]] if not b.empty else b),
                         ("Temiz", b[~b["bicak"]] if not b.empty else b)):
            if grup.empty:
                out.append(f"| {ad} | {donem} | 0 | — | — | — | — | — |")
                continue
            g = grup["getiri20"]
            ayrim[(ad, donem)] = g.mean()
            out.append(f"| {ad} | {donem} | {len(g)} | {_f(g.mean() * 100, 2)} | {_f(g.median() * 100, 2)} | "
                       f"{_f((g < 0).mean() * 100, 1)} | {_f(grup['endeks'].mean() * 100, 2)} | "
                       f"{_f((g - grup['endeks']).mean() * 100, 2)} |")

    # Uyarılar
    fr_t = sv["F_FIRSAT"]
    out += ["", "**Uyarılar** (sinyali engellemez; FIRSAT işlemleri uyarıya göre)", "",
            "| Uyarı | Dönem | Uyarılı sinyal | Beklenen R (uyarılı) | Uyarısız sinyal | Beklenen R (uyarısız) |",
            "|---|---|---:|---:|---:|---:|"]
    for key, ad in (("uyari_hisseye_ozel", "Hisseye özel düşüş (KAP'ı kontrol et)"),
                    ("uyari_piyasa", "Piyasa geneli satış (pozisyonu küçük tut)")):
        for donem in ("GELİŞTİRME", "TEST"):
            if fr_t.empty:
                continue
            var, yok = _r(fr_t[fr_t[key]], donem), _r(fr_t[~fr_t[key]], donem)
            out.append(f"| {ad} | {donem} | {var.get('sinyal', 0)} | {_f(var.get('beklenen_r'), 3)} | "
                       f"{yok.get('sinyal', 0)} | {_f(yok.get('beklenen_r'), 3)} |")

    # Eleme ayırıyor mu?
    karar = {}
    for donem in ("GELİŞTİRME", "TEST"):
        fr_r = _r(sv["F_FIRSAT"], donem).get("beklenen_r", np.nan)
        bc_r = _r(sv["F_BICAK"], donem).get("beklenen_r", np.nan)
        karar[donem] = {
            "islem": fr_r > bc_r,
            "bolum": ayrim.get(("Düşen bıçak riski", donem), np.nan) < ayrim.get(("Temiz", donem), np.nan),
            "fark_r": fr_r - bc_r,
        }
    ayiriyor = all(k["islem"] and k["bolum"] for k in karar.values())
    out += ["", "**Eleme gerçekten kötü hisseleri ayırıyor mu?**", "",
            "Ölçüt: iki dönemde de (1) elenen tetiklerin beklenen getirisi FIRSAT'tan düşük ve (2) düşen bıçak "
            "riski işaretli bölümlerin 20 günlük getirisi temiz bölümlerden düşük.", ""]
    for donem, k in karar.items():
        out.append(f"- {donem}: FIRSAT − elenen = {_f(k['fark_r'], 3)} R ({'✔' if k['islem'] else '✘'}); "
                   f"bölüm getirisi işaretli < temiz: {'✔' if k['bolum'] else '✘'}")
    out += ["", f"**Sonuç:** eleme {'iki dönemde de ayırıyor' if ayiriyor else 'iki dönemde birlikte ayırmıyor'}.", ""]
    ayar_satirlari, ayar = eleme_ayari(sv["F_TETIK"], sv["F_BOLUM"]) if not ayiriyor else ([], None)
    out += ayar_satirlari
    return out, {"ayiriyor": ayiriyor, "karar": karar, "ayar": ayar}


def _ayrim(t: pd.DataFrame, bayrak: pd.Series) -> float:
    """Temiz tetiklerin beklenen getirisi − işaretli tetiklerinki (pozitif: kriter kötüleri yakalıyor)."""
    return ev.ozet(t[~bayrak]).get("beklenen_r", np.nan) - ev.ozet(t[bayrak]).get("beklenen_r", np.nan)


def eleme_ayari(tetik: pd.DataFrame, bolum: pd.DataFrame) -> tuple[list[str], dict]:
    """Eleme ayırmadığında: kriter başına en fazla 3 eşik, seçim yalnızca GELİŞTİRME yıllarıyla."""
    out = ["### Düşen bıçak elemesinin ayarlanması (Kural 7)", "",
           "Her kriter için 3 eşik denendi. Seçim yalnızca GELİŞTİRME'de: her yıl için \"temiz tetiklerin beklenen "
           "getirisi − işaretli tetiklerinki\" hesaplandı (pozitif = kriter kötü tetikleri yakalıyor); en çok yılda "
           "pozitif olan eşik seçildi. Seçilen eşik GELİŞTİRME'nin tamamında da pozitif değilse kriter elemeden "
           "çıkarıldı. TEST'e yalnızca son elemeyi doğrulamak için bakıldı.", "",
           "| Kriter | Eşik | İşaretli tetik (GEL) | Temiz − işaretli (GEL, R) | Ayıran yıl | En kötü yıl | Seçildi |",
           "|---|---|---:|---:|---:|---:|:---:|"]
    gel = _donem(tetik, "GELİŞTİRME")
    secilen = {}
    for key, varyantlar in K_VARYANT.items():
        adaylar = []
        for etiket in varyantlar:
            col = f"{key}|{etiket}"
            yillik = {}
            for y in GEL_YILLARI:
                ty = gel[gel["tarih"].dt.year == y]
                yillik[y] = _ayrim(ty, ty[col]) if ty[col].any() and (~ty[col]).any() else np.nan
            adaylar.append((filtreler.yillik_tutarlilik(yillik), etiket, _ayrim(gel, gel[col]),
                            ev.ozet(gel[gel[col]]).get("sinyal", 0)))
        en_iyi = max(adaylar, key=lambda a: a[0])
        for (iyi, kotu), etiket, toplam, adet in adaylar:
            out.append(f"| {key} | {etiket} | {adet} | {_f(toplam, 3)} | {iyi}/4 | {_f(kotu, 3)} | "
                       f"{'✔' if etiket == en_iyi[1] else ''} |")
        if en_iyi[2] > 0:
            secilen[key] = en_iyi[1]

    out += ["", "**Ayarlanmış eleme:** " + (", ".join(f"{k} ({v})" for k, v in secilen.items()) if secilen
            else "hiçbir kriter GELİŞTİRME'de bile kötü tetikleri ayırmıyor; eleme kaldırılırsa FIRSAT = tüm tetikler."), ""]
    if not secilen:
        return out, {"secilen": {}}

    def bayrak(df: pd.DataFrame) -> pd.Series:
        return np.logical_or.reduce([df[f"{k}|{v}"] for k, v in secilen.items()])

    out += ["| Dönem | FIRSAT (ayarlı) sinyal | Beklenen R | Elenen sinyal | Beklenen R | İşaretli bölüm 20g % | Temiz bölüm 20g % | Ayırıyor mu |",
            "|---|---:|---:|---:|---:|---:|---:|---|"]
    sonuc = {"secilen": secilen}
    for donem in ("GELİŞTİRME", "TEST"):
        t, b = _donem(tetik, donem), _donem(bolum, donem)
        fl, bfl = bayrak(t), bayrak(b)
        temiz, elenen = ev.ozet(t[~fl]), ev.ozet(t[fl])
        b_isaretli, b_temiz = b.loc[bfl, "getiri20"].mean(), b.loc[~bfl, "getiri20"].mean()
        ayiriyor = temiz.get("beklenen_r", np.nan) > elenen.get("beklenen_r", np.nan) and b_isaretli < b_temiz
        sonuc[donem] = {"firsat": temiz, "elenen": elenen, "ayiriyor": bool(ayiriyor)}
        out.append(f"| {donem} | {temiz.get('sinyal', 0)} | {_f(temiz.get('beklenen_r'), 3)} | {elenen.get('sinyal', 0)} | "
                   f"{_f(elenen.get('beklenen_r'), 3)} | {_f(b_isaretli * 100, 2)} | {_f(b_temiz * 100, 2)} | "
                   f"{'✔' if ayiriyor else '✘'} |")
    out.append("")
    return out, sonuc


# ---------------------------------------------------------------------------
# Aşama 3d — portföy ve risk yönetimi
# ---------------------------------------------------------------------------

KOMBINASYONLAR = {
    "Sadece trend": ("trend",),
    "Sadece Fırsat": ("firsat",),
    "Trend + Fırsat": ("trend", "firsat"),
}
KIYASLAR = ("XU100 al-tut", "BIST 100 eşit ağırlıklı al-tut")


def _adaylar(t: pd.DataFrame, sistem: str) -> pd.DataFrame:
    """İşlem tablosundan portföy adayları: girişi olan (geçersiz olmayan) işlemler."""
    if t.empty:
        return pd.DataFrame()
    t = t[t["sonuc"].isin(ev.OUTCOMES + ("acik",)) & t["giris_tarihi"].notna()].copy()
    t["sistem"] = sistem
    t["cikis_tarihi"] = t["cikis_tarihi"].where(t["sonuc"] != "acik")
    return t[["kod", "sistem", "tarih", "giris_tarihi", "giris", "stop", "cikis_tarihi", "cikis", "oncelik"]]


def kapanis_tablosu(hisseler: dict, endeks: pd.DataFrame) -> pd.DataFrame:
    """Düzeltilmiş kapanışlar, tüm işlem günleri takviminde (hisse × gün)."""
    kapanis = {kod: motor_veri.motor_girdisi(df)["Close"] for kod, df in hisseler.items()}
    tablo = pd.DataFrame(kapanis)
    takvim = tablo.index.union(endeks.index)
    return tablo.reindex(takvim)


def not_oncelikli(t: pd.DataFrame, notlar: dict[str, str]) -> pd.DataFrame:
    """Trend adaylarının önceliği: önce not (A > B > C), sonra skor."""
    if t.empty or not notlar:
        return t
    t = t.copy()
    sira = {n: len(kalite.NOTLAR) - i for i, n in enumerate(kalite.NOTLAR)}  # A=3, B=2, C=1
    not_puani = [sira.get(notlar.get(kalite.grup_anahtari(s, None)), 0) for s in t["oncelik"]]
    t["oncelik"] = np.array(not_puani) * 1000 + t["oncelik"]
    return t


def asama3d(sonuc: dict, hisseler: dict, endeks: pd.DataFrame, kalite_ozet: dict) -> tuple[list[str], dict]:
    sv = sonuc["kisa"]
    kisa_not = kalite_ozet.get("kisa", {})
    notlar = kisa_not.get("notlar", {}) if kisa_not.get("gecerli") else {}
    adaylar = {"trend": not_oncelikli(_adaylar(sv["AL"], "trend"), notlar),
               "firsat": _adaylar(sv["F_FIRSAT"], "firsat")}
    kapanis = kapanis_tablosu(hisseler, endeks)
    rejim_df = portfoy.rejim(endeks)
    veri_sonu = kapanis.index[-1]

    seriler, ozetler, islem_sayisi = {}, {}, {}
    for donem, (bas, bit) in ev.DONEMLER.items():
        bit = min(bit, veri_sonu)
        seriler[donem], ozetler[donem], islem_sayisi[donem] = {}, {}, {}
        for ad, sistemler in KOMBINASYONLAR.items():
            a = pd.concat([adaylar[s] for s in sistemler], ignore_index=True)
            sermaye, kayit = portfoy.simule(a, kapanis, rejim_df, bas, bit)
            seriler[donem][ad] = sermaye
            islem_sayisi[donem][ad] = len(kayit)
        seriler[donem]["XU100 al-tut"] = portfoy.al_tut_endeks(endeks, bas, bit)
        seriler[donem]["BIST 100 eşit ağırlıklı al-tut"] = portfoy.al_tut_esit(kapanis, bas, bit)
        for ad, s in seriler[donem].items():
            ozetler[donem][ad] = portfoy.metrikler(s)

    out = [
        "## Aşama 3d — Portföy ve risk yönetimi",
        "",
        "Sinyal bazlı değil, portföy bazlı test. Her dönem **100.000 TL** ile, pozisyonsuz başlar (TEST, "
        "GELİŞTİRME'den pozisyon devralmaz). İşlemlerin giriş/çıkış fiyatları önceki aşamalardaki simülasyonun "
        "aynısıdır; portföy katmanı yalnızca hangi işlemin ve kaç adet alınacağına karar verir. Kurallar "
        "`portfoy.py` dosyasının başında.",
        "",
        "- **Risk:** işlem başına sermayenin %1'i (adet = sermaye × risk / (giriş − stop)); tek pozisyon en "
        "fazla %20; kaldıraç yok; en fazla 6 açık pozisyon, aynı hissede tek pozisyon.",
        "- **Oynaklık:** XU100'ün 20 günlük gerçekleşen oynaklığı son 1 yılın %80'lik diliminin üstündeyse risk %0,5.",
        "- **Piyasa filtresi:** XU100 < 50 günlük EMA iken trend sistemine yeni alım yok; FIRSAT'a izin var, risk %0,5.",
        "- **Sıralama:** yer yetmezse trend sinyalleri önce, FIRSAT sinyalleri sonra. Trend sinyalleri kendi içinde "
        "\"not ve skora göre\": Aşama 4'te not sistemi TEST'te doğrulandıysa önce not (A > B > C), sonra skor; "
        "doğrulanmadıysa yalnızca skor. FIRSAT'ın skoru yok; RSI(2) düşük olan önce (varsayım).",
        "- **Trend sistemi** kısa vade (günlük) AL'dır; haftalık orta vade bu günlük portföye dahil değil. "
        "**Destek** sistemi tanımlanmadığı için \"trend + Fırsat + Destek\" kombinasyonu yok.",
        "- **Metrikler:** Sharpe ve Sortino risksiz getiri 0 ile hesaplandı. TL mevduat faizi bu dönemde çok "
        "yüksek olduğu için bu oranlar olduğundan iyi görünür; asıl kıyas XU100 ve eşit ağırlıklı al-tut'tur. "
        "XU100 fiyat endeksidir (temettü içermez); hisseler ve eşit ağırlıklı al-tut temettü düzeltmelidir.",
        "- **Karar ölçütü:** önce TEST'te getiri / maksimum düşüş oranı, sonra toplam getiri.",
        "",
    ]
    for donem in ("TEST", "GELİŞTİRME"):
        bas, bit = ev.DONEMLER[donem]
        out += [f"**{donem}**{' ⬅ asıl sonuç' if donem == 'TEST' else ''} "
                f"({fmt_tarih(seriler[donem]['XU100 al-tut'].index[0])} – {fmt_tarih(seriler[donem]['XU100 al-tut'].index[-1])})", "",
                "| Portföy | İşlem | Toplam getiri % | Yıllık getiri % | Yıllık oynaklık % | Sharpe | Sortino | "
                "Maks. düşüş % | Düşüş süresi (gün) | Getiri / maks. düşüş |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for ad in list(KOMBINASYONLAR) + list(KIYASLAR):
            m = ozetler[donem][ad]
            out.append(
                f"| {ad} | {islem_sayisi[donem].get(ad, '—')} | {_f(m['toplam_getiri'] * 100, 1)} | "
                f"{_f(m['yillik_getiri'] * 100, 1)} | {_f(m['yillik_oynaklik'] * 100, 1)} | {_f(m['sharpe'], 2)} | "
                f"{_f(m['sortino'], 2)} | {_f(m['max_dusus'] * 100, 1)} | {m['max_dusus_suresi']} | "
                f"**{_f(m['getiri_dusus_orani'], 2)}** |")
        gunluk = pd.DataFrame({ad: seriler[donem][ad].pct_change() for ad in
                               ("Sadece trend", "Sadece Fırsat", "XU100 al-tut")}).dropna()
        korelasyon = gunluk.corr()
        out += ["", f"Günlük getiri korelasyonu ({donem}): trend–Fırsat {_f(korelasyon.iloc[0, 1], 2)}, "
                f"trend–XU100 {_f(korelasyon.iloc[0, 2], 2)}, Fırsat–XU100 {_f(korelasyon.iloc[1, 2], 2)}.", ""]

    test = ozetler["TEST"]
    sira = sorted(KOMBINASYONLAR, key=lambda ad: (-np.nan_to_num(test[ad]["getiri_dusus_orani"], nan=-np.inf),
                                                  -test[ad]["toplam_getiri"]))
    en_iyi = sira[0]
    xu = test["XU100 al-tut"]
    out += ["**Karar (TEST, önce getiri / maks. düşüş, sonra toplam getiri):** " + " > ".join(sira) + ". "
            f"En iyi kombinasyon **{en_iyi}**: getiri/düşüş {_f(test[en_iyi]['getiri_dusus_orani'], 2)}, toplam getiri "
            f"%{_f(test[en_iyi]['toplam_getiri'] * 100, 1)}. Aynı dönemde XU100 al-tut: getiri/düşüş "
            f"{_f(xu['getiri_dusus_orani'], 2)}, toplam %{_f(xu['toplam_getiri'] * 100, 1)}.", ""]

    performans_disa_aktar(seriler, ozetler, islem_sayisi, veri_sonu)
    return out, {"sira": sira}


def fmt_tarih(t: pd.Timestamp) -> str:
    return f"{t:%d.%m.%Y}"


def performans_disa_aktar(seriler: dict, ozetler: dict, islem_sayisi: dict, veri_sonu: pd.Timestamp) -> None:
    """Panelin Sistem Performansı sekmesi için sermaye serileri (CSV) ve metrikler (JSON)."""
    import json

    satirlar = [
        {"donem": donem, "tarih": f"{t:%Y-%m-%d}", "seri": ad, "sermaye": round(float(v), 2)}
        for donem, sozluk in seriler.items() for ad, s in sozluk.items() for t, v in s.dropna().items()
    ]
    pd.DataFrame(satirlar).to_csv(PERFORMANS_CSV, index=False, encoding="utf-8")

    def temiz(x):
        return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else float(x)

    meta = {
        "veri_sonu": f"{veri_sonu:%Y-%m-%d}",
        "olusturma": f"{date.today():%Y-%m-%d}",
        "baslangic_sermaye": portfoy.VARSAYILAN.sermaye,
        "kombinasyonlar": list(KOMBINASYONLAR),
        "kiyaslar": list(KIYASLAR),
        "metrikler": {donem: {ad: {k: temiz(v) for k, v in m.items()} | {"islem": islem_sayisi[donem].get(ad)}
                              for ad, m in d.items()} for donem, d in ozetler.items()},
    }
    PERFORMANS_JSON.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------------------
# Aşama 4 — sinyal kalitesi notu (kalibrasyon)
# ---------------------------------------------------------------------------

def asama4(sonuc: dict, kabuller: dict) -> tuple[list[str], dict]:
    import json

    out = [
        "## Aşama 4 — Sinyal kalitesi notu (kalibrasyon)",
        "",
        "Skora dayalı tahmin yerine geçmiş performansa dayalı not. GELİŞTİRME'deki AL sinyalleri skor aralığına "
        "(60-69, 70-79, 80+) ve vadenin kabul edilmiş alım filtrelerinden geçip geçmediğine göre gruplandı; gruplar "
        "GELİŞTİRME beklenen getirisine göre A, B, C notu aldı (grup 3'ten fazlaysa eşit dilimler). Notlar TEST'te "
        "doğrulandı: not ortalamaları TEST'te de A > B > C ise not sistemi geçerli, değilse panelde not gösterilmez. "
        "Makine öğrenmesi kullanılmadı.",
        "",
        "Paneldeki \"bu kalitedeki sinyallerin geçmişte %X'i hedefe ulaştı\" satırı grubun 2021'den bugüne tüm "
        "sinyallerinden hesaplanır (betimleyicidir; not ise yalnızca GELİŞTİRME'den belirlenir).",
        "",
    ]
    kalibrasyon, ozet = {}, {}
    for vade, bilgi in VADELER.items():
        t = sonuc[vade]["AL"].copy()
        kabul = {f: e for f, e in kabuller.get(vade, {}).items() if f != "F7"}
        filtreli = bool(kabul)
        if filtreli:
            t["filtre"] = np.logical_and.reduce([t[f"{f}|{e}"].to_numpy(dtype=bool) for f, e in kabul.items()])
        t["grup"] = [kalite.grup_anahtari(skor, bool(f) if filtreli else None)
                     for skor, f in zip(t["oncelik"], t["filtre"] if filtreli else [None] * len(t))]
        gel, test = _donem(t, "GELİŞTİRME"), _donem(t, "TEST")
        gruplar = sorted(g for g in t["grup"].dropna().unique())
        gel_r = {g: ev.ozet(gel[gel["grup"] == g]).get("beklenen_r", np.nan) for g in gruplar}
        notlar = kalite.not_ata(gel_r)
        t["not"] = t["grup"].map(notlar)
        gel, test = _donem(t, "GELİŞTİRME"), _donem(t, "TEST")
        not_r = {d: {n: ev.ozet(x[x["not"] == n]).get("beklenen_r", np.nan) for n in kalite.NOTLAR}
                 for d, x in (("GELİŞTİRME", gel), ("TEST", test))}
        gecerli = kalite.sira_tutuyor_mu(not_r["TEST"])
        ozet[vade] = {"gecerli": gecerli, "notlar": notlar}

        filtre_metni = (" ve " + ", ".join(f"{f} ({e})" for f, e in kabul.items())) if filtreli else ""
        out += [f"### {bilgi['ad']}", "",
                f"Gruplama: skor aralığı{filtre_metni}." if filtreli else "Gruplama: yalnızca skor aralığı "
                "(bu vadede kabul edilen filtre yok).", "",
                "| Grup | Not | GEL sinyal | GEL hedef % | GEL stop % | GEL beklenen R | TEST sinyal | TEST hedef % | "
                "TEST stop % | TEST beklenen R |",
                "|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for g in sorted(gruplar, key=lambda x: (notlar.get(x, "Z"), -gel_r.get(x, 0))):
            a, b = ev.ozet(gel[gel["grup"] == g]), ev.ozet(test[test["grup"] == g])
            out.append(f"| {g} | {notlar.get(g, '—')} | {a.get('sinyal', 0)} | {_f(a.get('hedef_pct'))} | "
                       f"{_f(a.get('stop_pct'))} | {_f(a.get('beklenen_r'), 3)} | {b.get('sinyal', 0)} | "
                       f"{_f(b.get('hedef_pct'))} | {_f(b.get('stop_pct'))} | {_f(b.get('beklenen_r'), 3)} |")
        out += ["", "| Not | GEL sinyal | GEL beklenen R | TEST sinyal | TEST beklenen R |", "|:---:|---:|---:|---:|---:|"]
        for n in kalite.NOTLAR:
            a, b = ev.ozet(gel[gel["not"] == n]), ev.ozet(test[test["not"] == n])
            out.append(f"| {n} | {a.get('sinyal', 0)} | {_f(a.get('beklenen_r'), 3)} | {b.get('sinyal', 0)} | "
                       f"{_f(b.get('beklenen_r'), 3)} |")
        karar = ("A > B > C sıralaması TEST'te de tutuyor; not sistemi panelde kullanılır." if gecerli else
                 "sıralama TEST'te tutmuyor; not sistemi kullanılmaz, panelde yalnızca tarihsel istatistik gösterilir.")
        out += ["", f"**TEST doğrulaması:** {karar}", ""]

        donem_ici = t[t["tarih"] >= ev.GELISTIRME[0]]
        kalibrasyon[vade] = {
            "gecerli": bool(gecerli),
            "filtreli": filtreli,
            "gruplar": {g: {"not": notlar.get(g), **kalite.istatistik(donem_ici[donem_ici["grup"] == g])}
                        for g in gruplar},
        }
    kalibrasyon["olusturma"] = f"{date.today():%Y-%m-%d}"
    kalite.DOSYA.write_text(json.dumps(kalibrasyon, ensure_ascii=False, indent=1), encoding="utf-8")
    return out, ozet


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
    ozet = rapor_yaz(sonuc, endeks, hisseler, veri_bitis)
    print("Kabul edilen filtreler:", ozet.pop("kabuller"))
    print("FIRSAT eleme:", ozet.pop("firsat"))
    print("Portföy:", ozet.pop("portfoy"))
    print("Kalite notu:", ozet.pop("kalite"))
    for vade in ozet:
        for donem in ozet[vade]:
            s = ozet[vade][donem]
            print(vade, donem, {k: (v.get("sinyal"), _f(v.get("beklenen_r"), 3)) for k, v in s.items()})
    print("Yazıldı:", REPORT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
