# BIST Sinyal Sistemi Raporu

> Eğitim amaçlıdır, yatırım tavsiyesi değildir. Geçmiş performans gelecek için garanti değildir.

Bu dosya `python tools/sistem_raporu.py` ile üretilir; elle düzenlemeyin. Veri sonu: **17.11.2026**.

## Metodoloji

- **Evren:** 100 hisse, Borsa İstanbul'un 2026-11-17 tarihli BIST 100 listesi; Yahoo Finance günlük verisi, 10 yıl.
- **Fiyat:** temettü düzeltmeli (Adj Close / Close) ve bölünme/bedelsiz onarımlı (`motor_veri.bolunme_onar`; açılış ±%10 limit dışındaysa kurumsal işlem sayılır).
- **Dönemler (sinyal tarihine göre):** GELİŞTİRME 01.01.2021–31.12.2024, TEST 01.01.2025–bugün. Göstergeler daha eski veriyle ısınır; hissenin ilk 120 günü (orta vadede 52 haftası) sinyal olarak alınmaz.
- **Giriş:** sinyal barının ertesi barının açılışı. **Stop / hedef:** sinyal barındaki motor seviyeleri (stop = kapanış − 1,5 ATR, hedef = kapanış + 3 ATR; orta vadede 2 ATR ve 4 ATR). Aynı barda hem stop hem hedef görülürse stop sayılır. Stop/hedefin ötesinde açılan barda çıkış açılıştan.
- **Zaman aşımı:** kısa vadede 20 işlem günü, orta vadede 12 hafta (giriş barı dahil); son barın kapanışından çıkış.
- **Satış sinyalleri (SAT, KAR AL, ÇIK)** açığa satış gibi değerlendirilir: stop = kapanış + 1,5 ATR, hedef = kapanış − 3 ATR. Soru: sinyalden sonra fiyat düştü mü?
- **Maliyet:** her işleme gidiş-dönüş %0,2. **1R** = giriş ile stop arası mesafe; R getirileri maliyet sonrasıdır.
- **Rastgele gün:** aynı hisselerde, aynı dönemde **her** bardan aynı kurallarla (aynı stop/hedef formülü, aynı zaman aşımı) giriş. Bir sinyal ancak bundan iyiyse bilgi taşır.
- **XU100:** her işlem için endeksin aynı giriş-çıkış tarihlerindeki getirisi ve dönem boyunca al-tut getirisi.
- **Açık** (zaman penceresi henüz dolmamış) ve **geçersiz** (giriş açılışı stop/hedefin ötesinde) işlemler metriklere girmez; sayıları tablonun altında.

## Aşama 1 — Başlangıç ölçümü (filtresiz sistem)

Bu bölüm kıyas noktasıdır: sonraki aşamalardaki filtreler bu rakamlara göre değerlendirilir.

### Kısa vade (günlük)

**TEST** ⬅ asıl sonuç · XU100 al-tut: 19,3%

| Sinyal | Sinyal sayısı | Hedef % | Stop % | Zaman aşımı % | Beklenen getiri (R) | Kâr faktörü | Ort. net getiri % | Hedefe medyan gün (Q1–Q3) | En uzun kayıp serisi | XU100 aynı tarihlerde % | XU100'e göre fark % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AL | 350 | 30,9 | 63,4 | 5,7 | **-0,138** | 0,80 | -0,62 | 6 (3–10) | 19 | -0,38 | -0,04 |
| Rastgele gün (alım, aynı kurallar) | 45120 | 31,1 | 56,3 | 12,6 | **0,018** | 1,03 | 0,05 | 8 (5–12) | 332 | 0,29 | -0,05 |
| SAT | 217 | 22,1 | 63,1 | 14,7 | **-0,102** | 0,85 | -0,73 | 10 (5–15) | 23 | 0,65 | 0,13 |
| KAR AL | 406 | 25,9 | 55,2 | 19,0 | **0,045** | 1,07 | 0,29 | 10 (6–15) | 18 | 0,11 | 0,63 |
| ÇIK | 905 | 23,5 | 56,9 | 19,6 | **-0,050** | 0,92 | -0,18 | 8 (4–12) | 26 | 0,28 | 0,29 |
| Rastgele gün (satış, aynı kurallar) | 45446 | 23,1 | 61,8 | 15,1 | **-0,084** | 0,87 | -0,38 | 9 (6–14) | 136 | 0,37 | 0,20 |

Açık / geçersiz işlem sayısı: AL 8/0, RASTGELE_AL 1143/234, SAT 5/0, KAR_AL 6/0, CIK 3/0, RASTGELE_SAT 924/127

**GELİŞTİRME** · XU100 al-tut: 563,2%

| Sinyal | Sinyal sayısı | Hedef % | Stop % | Zaman aşımı % | Beklenen getiri (R) | Kâr faktörü | Ort. net getiri % | Hedefe medyan gün (Q1–Q3) | En uzun kayıp serisi | XU100 aynı tarihlerde % | XU100'e göre fark % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AL | 578 | 45,0 | 44,8 | 10,2 | **0,374** | 1,76 | 1,68 | 8 (5–13) | 19 | 2,02 | -0,13 |
| Rastgele gün (alım, aynı kurallar) | 84298 | 39,4 | 47,8 | 12,8 | **0,247** | 1,46 | 1,54 | 8 (5–12) | 340 | 1,30 | 0,47 |
| SAT | 297 | 19,2 | 58,2 | 22,6 | **0,134** | 1,22 | -0,29 | 12 (7–15) | 21 | 0,89 | 0,82 |
| KAR AL | 675 | 23,1 | 60,0 | 16,9 | **-0,049** | 0,92 | -0,43 | 9 (5–14) | 32 | 0,24 | 0,03 |
| ÇIK | 1496 | 17,5 | 63,6 | 18,9 | **-0,135** | 0,80 | -1,60 | 9 (4–14) | 59 | 1,30 | -0,15 |
| Rastgele gün (satış, aynı kurallar) | 84360 | 18,0 | 68,3 | 13,7 | **-0,254** | 0,66 | -1,43 | 10 (6–14) | 672 | 0,98 | -0,29 |

Açık / geçersiz işlem sayısı: AL 0/7, RASTGELE_AL 0/333, SAT 0/0, KAR_AL 0/2, CIK 0/8, RASTGELE_SAT 0/271

### Orta vade (haftalık)

**TEST** ⬅ asıl sonuç · XU100 al-tut: 19,3%

| Sinyal | Sinyal sayısı | Hedef % | Stop % | Zaman aşımı % | Beklenen getiri (R) | Kâr faktörü | Ort. net getiri % | Hedefe medyan hafta (Q1–Q3) | En uzun kayıp serisi | XU100 aynı tarihlerde % | XU100'e göre fark % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AL | 93 | 21,5 | 52,7 | 25,8 | **-0,074** | 0,88 | -1,52 | 7 (5–10) | 9 | 0,23 | -1,55 |
| Rastgele gün (alım, aynı kurallar) | 8822 | 17,1 | 33,4 | 49,5 | **0,116** | 1,28 | 1,86 | 8 (5–10) | 357 | 2,47 | -0,40 |
| SAT | 41 | 2,4 | 43,9 | 53,7 | **-0,391** | 0,34 | -7,31 | 10 (10–10) | 16 | 3,56 | -3,55 |
| KAR AL | 80 | 0,0 | 40,0 | 60,0 | **-0,232** | 0,52 | -4,23 | — | 11 | 5,49 | 1,46 |
| ÇIK | 187 | 1,1 | 47,1 | 51,9 | **-0,341** | 0,37 | -6,58 | 5 (4–6) | 13 | 5,75 | -0,62 |
| Rastgele gün (satış, aynı kurallar) | 8514 | 4,1 | 47,9 | 47,9 | **-0,197** | 0,63 | -3,35 | 8 (6–10) | 60 | 3,39 | 0,24 |

Açık / geçersiz işlem sayısı: AL 1/0, RASTGELE_AL 717/0, SAT 10/0, KAR_AL 10/0, CIK 32/0, RASTGELE_SAT 1025/0

**GELİŞTİRME** · XU100 al-tut: 563,2%

| Sinyal | Sinyal sayısı | Hedef % | Stop % | Zaman aşımı % | Beklenen getiri (R) | Kâr faktörü | Ort. net getiri % | Hedefe medyan hafta (Q1–Q3) | En uzun kayıp serisi | XU100 aynı tarihlerde % | XU100'e göre fark % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AL | 111 | 45,0 | 27,9 | 27,0 | **0,669** | 3,14 | 10,45 | 4 (3–7) | 8 | 11,22 | -0,57 |
| Rastgele gün (alım, aynı kurallar) | 17294 | 32,2 | 24,1 | 43,7 | **0,504** | 2,66 | 8,77 | 7 (4–9) | 44 | 8,35 | 0,62 |
| SAT | 47 | 0,0 | 55,3 | 44,7 | **-0,443** | 0,29 | -8,09 | — | 17 | 7,55 | -0,34 |
| KAR AL | 105 | 0,0 | 44,8 | 55,2 | **-0,312** | 0,39 | -5,41 | — | 17 | 4,68 | -0,53 |
| ÇIK | 352 | 1,1 | 51,1 | 47,7 | **-0,353** | 0,38 | -6,74 | 10 (10–11) | 26 | 6,73 | 0,19 |
| Rastgele gün (satış, aynı kurallar) | 17294 | 3,0 | 59,0 | 37,9 | **-0,407** | 0,37 | -6,86 | 8 (6–10) | 520 | 6,46 | -0,20 |

Açık / geçersiz işlem sayısı: AL 0/0, RASTGELE_AL 0/0, SAT 0/0, KAR_AL 0/0, CIK 0/0, RASTGELE_SAT 0/0

### Ana bulgular (beklenen getiri, sinyal − rastgele gün)

| Vade | Sinyal | GELİŞTİRME fark (R) | TEST fark (R) | Yorum |
|---|---|---:|---:|---|
| Kısa vade (günlük) | AL | 0,127 | -0,156 | GELİŞTİRME'de iyi, TEST'te rastgeleden kötü |
| Kısa vade (günlük) | SAT | 0,387 | -0,018 | GELİŞTİRME'de iyi, TEST'te rastgeleden kötü |
| Kısa vade (günlük) | KAR AL | 0,205 | 0,129 | iki dönemde de rastgeleden iyi |
| Kısa vade (günlük) | ÇIK | 0,118 | 0,034 | iki dönemde de rastgeleden iyi |
| Orta vade (haftalık) | AL | 0,164 | -0,190 | GELİŞTİRME'de iyi, TEST'te rastgeleden kötü |
| Orta vade (haftalık) | SAT | -0,036 | -0,193 | iki dönemde de rastgeleden kötü |
| Orta vade (haftalık) | KAR AL | 0,095 | -0,035 | GELİŞTİRME'de iyi, TEST'te rastgeleden kötü |
| Orta vade (haftalık) | ÇIK | 0,054 | -0,144 | GELİŞTİRME'de iyi, TEST'te rastgeleden kötü |

## Sınırlamalar

- **Hayatta kalma yanlılığı:** test evreni bugünkü BIST 100 listesidir. Geçmişte endekste olup çıkarılan, iflas eden ya da işlemden kaldırılan hisseler yoktur; endekse sonradan girenler genelde iyi performans gösterdiği için girmiştir. Sonuçlar bu yüzden olduğundan iyi görünebilir.
- Bazı hisseler borsaya 2021'den sonra girdi; GELİŞTİRME döneminde daha az hisse vardır.
- Bölünme/bedelsiz onarımında oran açılış boşluğundan tahmin edilir; hata en fazla o geceki gerçek piyasa hareketi kadardır. Limit içinde kalan küçük bedelli/bedelsizler onarılmaz.
- Gün içi fiyat sırası bilinmez: aynı barda stop ve hedef görüldüyse stop sayılır (kötümser).
- Likidite, tavan/taban kilidinde işlem yapılamaması ve açığa satış kısıtları modellenmemiştir.
- Rastgele gün kıyası her barı kullanır; ardışık günlerin işlemleri birbirinden bağımsız değildir.

