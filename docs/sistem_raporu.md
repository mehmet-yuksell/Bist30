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

## Aşama 2 — Alım sinyali kalite filtreleri

Her filtre başlangıç sistemine **tek başına** eklendi. Eşik seçimi yalnızca GELİŞTİRME verisiyle yapıldı: her eşik için 2021, 2022, 2023 ve 2024 yıllarında beklenen getirinin başlangıca göre farkı hesaplandı; **en çok yılda iyileştiren** eşik seçildi (eşitlikte en kötü yıldaki fark büyük olan). TEST sonucuna yalnızca seçilen eşik için, kabul kararı aşamasında bakıldı; seçilmeyen eşiklerin TEST sonucu bu yüzden tabloda yok.

Kabul şartları (üçü birlikte): (a) TEST'te beklenen getiriyi artırır, (b) GELİŞTİRME'de de artırır, (c) TEST'te en az 30 sinyal bırakır.

> **Çoklu deneme uyarısı:** 8 filtre × 2 vade denendi. Bunlardan bazıları yalnızca şans eseri iki dönemde de olumlu çıkabilir. Kabul edilen bir filtre "kanıtlanmış iyileşme" değil, bu kurallardan geçmiş bir adaydır.

### Kısa vade (günlük)

Başlangıç: GELİŞTİRME 578 sinyal, 0,374 R (standart hata ±0,061) · TEST 350 sinyal, -0,138 R (standart hata ±0,072). Standart hatadan küçük farklar gürültüden ayırt edilemez.

**Eşik seçimi (yalnızca GELİŞTİRME)**

| Filtre | Eşik | Sinyal | Beklenen R | Fark (R) | İyileşen yıl | En kötü yıl farkı | Seçildi |
|---|---|---:|---:|---:|---:|---:|:---:|
| F1 | EMA 20 | 500 | 0,391 | 0,017 | 2/4 | -0,018 |  |
| F1 | EMA 50 | 482 | 0,433 | 0,059 | 3/4 | -0,035 | ✔ |
| F1 | EMA 100 | 496 | 0,386 | 0,012 | 2/4 | -0,087 |  |
| F2 | +0 puan | 209 | 0,305 | -0,069 | 1/4 | -0,093 |  |
| F2 | +2 puan | 168 | 0,332 | -0,042 | 2/4 | -0,137 |  |
| F2 | +5 puan | 120 | 0,318 | -0,056 | 3/4 | -0,230 | ✔ |
| F3 | 2,0 ATR | 350 | 0,337 | -0,037 | 2/4 | -0,143 |  |
| F3 | 2,5 ATR | 468 | 0,377 | 0,003 | 2/4 | -0,073 |  |
| F3 | 3,0 ATR | 532 | 0,395 | 0,021 | 2/4 | -0,010 | ✔ |
| F4 | 10 mn TL | 568 | 0,360 | -0,014 | 0/4 | -0,033 |  |
| F4 | 20 mn TL | 543 | 0,347 | -0,027 | 1/4 | -0,056 | ✔ |
| F4 | 50 mn TL | 480 | 0,338 | -0,036 | 1/4 | -0,058 |  |
| F5 | EMA 100 | 578 | 0,374 | 0,000 | 0/4 | 0,000 |  |
| F5 | EMA 200 | 560 | 0,363 | -0,011 | 2/4 | -0,056 | ✔ |
| F5 | EMA 300 | 561 | 0,364 | -0,010 | 1/4 | -0,058 |  |
| F6 | %3 | 544 | 0,396 | 0,022 | 3/4 | -0,001 | ✔ |
| F6 | %5 | 564 | 0,382 | 0,008 | 2/4 | -0,004 |  |
| F6 | %7 | 571 | 0,383 | 0,009 | 1/4 | -0,003 |  |
| F7 | en düşük | 524 | 0,342 | -0,032 | 1/4 | -0,054 |  |
| F7 | orta nokta | 398 | 0,375 | 0,001 | 2/4 | -0,015 | ✔ |
| F7 | kapanış | 304 | 0,256 | -0,118 | 0/4 | -0,239 |  |
| F8 | %7 | 500 | 0,412 | 0,038 | 4/4 | 0,003 | ✔ |
| F8 | %8,5 | 523 | 0,391 | 0,017 | 3/4 | -0,003 |  |
| F8 | %9,5 | 534 | 0,384 | 0,010 | 4/4 | 0,000 |  |

**Kabul kararı**

| Filtre | Tanım | Seçilen eşik | GEL fark (R) | TEST fark (R) | TEST sinyal | Karar | Gerekçe |
|---|---|---|---:|---:|---:|---|---|
| F1 | Piyasa rejimi: XU100 kapanışı N günlük EMA'nın üstünde | EMA 50 | 0,059 | -0,030 | 289 | Red | TEST'te beklenen getiriyi artırmıyor |
| F2 | Göreceli güç: hissenin 20 ve 60 günlük getirisi XU100'den en az X puan yüksek | +5 puan | -0,056 | 0,212 | 69 | Red | GELİŞTİRME'de artırmıyor |
| F3 | Aşırı uzama yok: fiyat yavaş EMA'dan en fazla K ATR uzakta | 3,0 ATR | 0,021 | -0,034 | 322 | Red | TEST'te beklenen getiriyi artırmıyor |
| F4 | Likidite: 20 günlük ortalama işlem hacmi (fiyat × adet) en az X TL | 20 mn TL | -0,027 | 0,000 | 350 | Red | TEST'te beklenen getiriyi artırmıyor; GELİŞTİRME'de artırmıyor |
| F5 | Uzun vadeli trend: fiyat N günlük EMA'nın üstünde | EMA 200 | -0,011 | 0,029 | 307 | Red | GELİŞTİRME'de artırmıyor |
| F6 | Boşluk yok: sinyal günü açılış boşluğu en fazla %X | %3 | 0,022 | -0,023 | 330 | Red | TEST'te beklenen getiriyi artırmıyor |
| F7 | Teyit günü: ertesi gün kapanış sinyal gününün seviyesinin altına inmezse gir (giriş 1 bar gecikir) | orta nokta | 0,001 | -0,082 | 240 | Red | TEST'te beklenen getiriyi artırmıyor |
| F8 | Tavan yok: sinyal günü yükselişi %X'in altında | %7 | 0,038 | -0,056 | 307 | Red | TEST'te beklenen getiriyi artırmıyor |

**Önce / sonra — TEST** ⬅ asıl sonuç

| Sinyal | Sinyal sayısı | Hedef % | Stop % | Zaman aşımı % | Beklenen getiri (R) | Kâr faktörü | Ort. net getiri % | Hedefe medyan gün (Q1–Q3) | En uzun kayıp serisi | XU100 aynı tarihlerde % | XU100'e göre fark % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Başlangıç (filtresiz) | 350 | 30,9 | 63,4 | 5,7 | **-0,138** | 0,80 | -0,62 | 6 (3–10) | 19 | -0,38 | -0,04 |
| F1 (EMA 50) | 289 | 29,4 | 64,4 | 6,2 | **-0,168** | 0,77 | -0,83 | 6 (4–10) | 29 | -0,43 | -0,20 |
| F2 (+5 puan) | 69 | 40,6 | 55,1 | 4,3 | **0,074** | 1,13 | 0,55 | 4 (2–8) | 7 | -0,07 | 0,82 |
| F3 (3,0 ATR) | 322 | 28,9 | 64,9 | 6,2 | **-0,172** | 0,76 | -0,89 | 6 (4–10) | 18 | -0,37 | -0,32 |
| F4 (20 mn TL) | 350 | 30,9 | 63,4 | 5,7 | **-0,138** | 0,80 | -0,62 | 6 (3–10) | 19 | -0,38 | -0,04 |
| F5 (EMA 200) | 307 | 31,6 | 62,5 | 5,9 | **-0,110** | 0,84 | -0,48 | 6 (3–10) | 16 | -0,28 | 0,00 |
| F6 (%3) | 330 | 30,0 | 64,2 | 5,8 | **-0,162** | 0,77 | -0,77 | 6 (3–10) | 19 | -0,44 | -0,13 |
| F7 (orta nokta) | 240 | 37,1 | 57,5 | 5,4 | **-0,220** | 0,66 | -1,16 | 6 (3–10) | 13 | -0,48 | -0,48 |
| F8 (%7) | 307 | 27,7 | 66,1 | 6,2 | **-0,194** | 0,74 | -1,02 | 6 (4–10) | 18 | -0,47 | -0,35 |

**Önce / sonra — GELİŞTİRME**

| Sinyal | Sinyal sayısı | Hedef % | Stop % | Zaman aşımı % | Beklenen getiri (R) | Kâr faktörü | Ort. net getiri % | Hedefe medyan gün (Q1–Q3) | En uzun kayıp serisi | XU100 aynı tarihlerde % | XU100'e göre fark % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Başlangıç (filtresiz) | 578 | 45,0 | 44,8 | 10,2 | **0,374** | 1,76 | 1,68 | 8 (5–13) | 19 | 2,02 | -0,13 |
| F1 (EMA 50) | 482 | 47,7 | 42,5 | 9,8 | **0,433** | 1,92 | 1,99 | 8 (5–13) | 13 | 2,19 | 0,00 |
| F2 (+5 puan) | 120 | 42,5 | 47,5 | 10,0 | **0,318** | 1,62 | 1,73 | 10 (5–14) | 11 | 2,26 | -0,33 |
| F3 (3,0 ATR) | 532 | 45,3 | 43,6 | 11,1 | **0,395** | 1,82 | 1,79 | 8 (5–13) | 19 | 2,07 | -0,07 |
| F4 (20 mn TL) | 543 | 44,0 | 45,9 | 10,1 | **0,347** | 1,69 | 1,50 | 8 (5–13) | 19 | 1,79 | -0,08 |
| F5 (EMA 200) | 560 | 44,3 | 45,2 | 10,5 | **0,363** | 1,73 | 1,63 | 8 (5–13) | 19 | 2,03 | -0,20 |
| F6 (%3) | 544 | 45,6 | 44,1 | 10,3 | **0,396** | 1,82 | 1,84 | 8 (5–13) | 19 | 2,04 | 0,01 |
| F7 (orta nokta) | 398 | 55,8 | 35,7 | 8,5 | **0,375** | 1,97 | 1,92 | 7 (4–13) | 10 | 1,81 | 0,31 |
| F8 (%7) | 500 | 46,0 | 44,0 | 10,0 | **0,412** | 1,86 | 1,91 | 8 (5–13) | 22 | 2,21 | -0,09 |

**F7 teyit gününün gecikme maliyeti** (aynı teyitli sinyaller: ertesi gün girişe karşı bir gün bekleyip giriş)

> "Hemen giriş" gerçekte yapılamaz: teyit ertesi günün kapanışında bilinir, o güne girmek geleceği bilmek olur. Bu sütun yalnızca gecikmenin maliyetini ölçmek için vardır; F7'nin kendi sonucu "gecikmeli giriş"tir.

| Teyit seviyesi | Dönem | Sinyal | Hemen giriş R | Gecikmeli giriş R | Gecikmenin etkisi (R) |
|---|---|---:|---:|---:|---:|
| en düşük | GELİŞTİRME | 524 | 0,446 | 0,342 | -0,104 |
| en düşük | TEST | 299 | -0,060 | -0,218 | -0,158 |
| orta nokta | GELİŞTİRME | 398 | 0,590 | 0,375 | -0,215 |
| orta nokta | TEST | 240 | 0,023 | -0,220 | -0,243 |
| kapanış | GELİŞTİRME | 304 | 0,641 | 0,256 | -0,385 |
| kapanış | TEST | 177 | 0,184 | -0,186 | -0,370 |

**Birleşik sonuç:** bu vadede kabul edilen filtre yok.

### Orta vade (haftalık)

Başlangıç: GELİŞTİRME 111 sinyal, 0,669 R (standart hata ±0,120) · TEST 93 sinyal, -0,074 R (standart hata ±0,129). Standart hatadan küçük farklar gürültüden ayırt edilemez.

**Eşik seçimi (yalnızca GELİŞTİRME)**

| Filtre | Eşik | Sinyal | Beklenen R | Fark (R) | İyileşen yıl | En kötü yıl farkı | Seçildi |
|---|---|---:|---:|---:|---:|---:|:---:|
| F1 | EMA 20 | 104 | 0,687 | 0,018 | 1/4 | -0,035 |  |
| F1 | EMA 50 | 105 | 0,681 | 0,013 | 1/4 | -0,035 |  |
| F1 | EMA 100 | 107 | 0,677 | 0,008 | 1/4 | -0,019 | ✔ |
| F2 | +0 puan | 55 | 0,622 | -0,046 | 2/4 | -0,087 |  |
| F2 | +2 puan | 49 | 0,685 | 0,017 | 3/4 | -0,014 | ✔ |
| F2 | +5 puan | 41 | 0,575 | -0,094 | 2/4 | -0,163 |  |
| F3 | 2,0 ATR | 75 | 0,580 | -0,089 | 1/4 | -0,254 |  |
| F3 | 2,5 ATR | 93 | 0,608 | -0,061 | 0/4 | -0,162 |  |
| F3 | 3,0 ATR | 104 | 0,658 | -0,010 | 1/4 | -0,052 | ✔ |
| F4 | 10 mn TL | 110 | 0,657 | -0,012 | 0/4 | -0,040 | ✔ |
| F4 | 20 mn TL | 107 | 0,633 | -0,036 | 0/4 | -0,040 |  |
| F4 | 50 mn TL | 97 | 0,615 | -0,054 | 0/4 | -0,072 |  |
| F5 | EMA 100 | 111 | 0,669 | 0,000 | 0/4 | 0,000 |  |
| F5 | EMA 200 | 111 | 0,669 | 0,000 | 0/4 | 0,000 |  |
| F5 | EMA 300 | 110 | 0,684 | 0,015 | 1/4 | 0,000 | ✔ |
| F6 | %3 | 110 | 0,679 | 0,010 | 1/4 | 0,000 | ✔ |
| F6 | %5 | 111 | 0,669 | 0,000 | 0/4 | 0,000 |  |
| F6 | %7 | 111 | 0,669 | 0,000 | 0/4 | 0,000 |  |
| F7 | en düşük | 105 | 0,495 | -0,174 | 1/4 | -0,326 | ✔ |
| F7 | orta nokta | 86 | 0,479 | -0,189 | 1/4 | -0,451 |  |
| F7 | kapanış | 62 | 0,425 | -0,243 | 1/4 | -0,700 |  |
| F8 | %7 | 104 | 0,687 | 0,018 | 2/4 | -0,123 |  |
| F8 | %8,5 | 108 | 0,692 | 0,023 | 2/4 | -0,050 | ✔ |
| F8 | %9,5 | 108 | 0,692 | 0,023 | 2/4 | -0,050 |  |

**Kabul kararı**

| Filtre | Tanım | Seçilen eşik | GEL fark (R) | TEST fark (R) | TEST sinyal | Karar | Gerekçe |
|---|---|---|---:|---:|---:|---|---|
| F1 | Piyasa rejimi: XU100 kapanışı N günlük EMA'nın üstünde | EMA 100 | 0,008 | 0,017 | 85 | **Kabul** | üç şart da sağlandı |
| F2 | Göreceli güç: hissenin 20 ve 60 günlük getirisi XU100'den en az X puan yüksek | +2 puan | 0,017 | -0,205 | 57 | Red | TEST'te beklenen getiriyi artırmıyor |
| F3 | Aşırı uzama yok: fiyat yavaş EMA'dan en fazla K ATR uzakta | 3,0 ATR | -0,010 | 0,021 | 91 | Red | GELİŞTİRME'de artırmıyor |
| F4 | Likidite: 20 günlük ortalama işlem hacmi (fiyat × adet) en az X TL | 10 mn TL | -0,012 | 0,000 | 93 | Red | TEST'te beklenen getiriyi artırmıyor; GELİŞTİRME'de artırmıyor |
| F5 | Uzun vadeli trend: fiyat N günlük EMA'nın üstünde | EMA 300 | 0,015 | 0,019 | 91 | **Kabul** | üç şart da sağlandı |
| F6 | Boşluk yok: sinyal günü açılış boşluğu en fazla %X | %3 | 0,010 | -0,004 | 89 | Red | TEST'te beklenen getiriyi artırmıyor |
| F7 | Teyit günü: ertesi gün kapanış sinyal gününün seviyesinin altına inmezse gir (giriş 1 bar gecikir) | en düşük | -0,174 | 0,270 | 83 | Red | GELİŞTİRME'de artırmıyor |
| F8 | Tavan yok: sinyal günü yükselişi %X'in altında | %8,5 | 0,023 | 0,014 | 89 | **Kabul** | üç şart da sağlandı |

**Önce / sonra — TEST** ⬅ asıl sonuç

| Sinyal | Sinyal sayısı | Hedef % | Stop % | Zaman aşımı % | Beklenen getiri (R) | Kâr faktörü | Ort. net getiri % | Hedefe medyan hafta (Q1–Q3) | En uzun kayıp serisi | XU100 aynı tarihlerde % | XU100'e göre fark % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Başlangıç (filtresiz) | 93 | 21,5 | 52,7 | 25,8 | **-0,074** | 0,88 | -1,52 | 7 (5–10) | 9 | 0,23 | -1,55 |
| F1 (EMA 100) ✔ | 85 | 22,4 | 54,1 | 23,5 | **-0,056** | 0,91 | -1,36 | 7 (4–10) | 9 | -0,15 | -1,00 |
| F2 (+2 puan) | 57 | 14,0 | 57,9 | 28,1 | **-0,279** | 0,57 | -4,26 | 6 (4–10) | 12 | 0,11 | -4,17 |
| F3 (3,0 ATR) | 91 | 22,0 | 51,6 | 26,4 | **-0,053** | 0,91 | -1,17 | 7 (5–10) | 9 | 0,41 | -1,39 |
| F4 (10 mn TL) | 93 | 21,5 | 52,7 | 25,8 | **-0,074** | 0,88 | -1,52 | 7 (5–10) | 9 | 0,23 | -1,55 |
| F5 (EMA 300) ✔ | 91 | 22,0 | 52,7 | 25,3 | **-0,055** | 0,91 | -1,20 | 7 (5–10) | 9 | 0,38 | -1,38 |
| F6 (%3) | 89 | 21,3 | 52,8 | 25,8 | **-0,078** | 0,87 | -1,66 | 7 (4–10) | 9 | 0,30 | -1,76 |
| F7 (en düşük) | 83 | 25,3 | 53,0 | 21,7 | **0,196** | 1,34 | 0,31 | 7 (5–11) | 15 | 0,11 | 0,40 |
| F8 (%8,5) ✔ | 89 | 21,3 | 51,7 | 27,0 | **-0,060** | 0,90 | -1,31 | 7 (4–10) | 9 | 0,37 | -1,48 |
| Kabul edilenlerin hepsi birlikte: F1, F5, F8 | 79 | 22,8 | 53,2 | 24,1 | **-0,018** | 0,97 | -0,74 | 7 (4–11) | 9 | 0,15 | -0,69 |

**Önce / sonra — GELİŞTİRME**

| Sinyal | Sinyal sayısı | Hedef % | Stop % | Zaman aşımı % | Beklenen getiri (R) | Kâr faktörü | Ort. net getiri % | Hedefe medyan hafta (Q1–Q3) | En uzun kayıp serisi | XU100 aynı tarihlerde % | XU100'e göre fark % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Başlangıç (filtresiz) | 111 | 45,0 | 27,9 | 27,0 | **0,669** | 3,14 | 10,45 | 4 (3–7) | 8 | 11,22 | -0,57 |
| F1 (EMA 100) ✔ | 107 | 45,8 | 28,0 | 26,2 | **0,677** | 3,15 | 10,65 | 4 (3–7) | 8 | 10,77 | 0,08 |
| F2 (+2 puan) | 49 | 44,9 | 28,6 | 26,5 | **0,685** | 3,20 | 10,98 | 4 (2–6) | 4 | 10,14 | 1,04 |
| F3 (3,0 ATR) | 104 | 44,2 | 27,9 | 27,9 | **0,658** | 3,11 | 10,43 | 5 (4–7) | 8 | 11,43 | -0,80 |
| F4 (10 mn TL) | 110 | 44,5 | 28,2 | 27,3 | **0,657** | 3,08 | 10,38 | 5 (3–7) | 8 | 11,17 | -0,59 |
| F5 (EMA 300) ✔ | 110 | 45,5 | 27,3 | 27,3 | **0,684** | 3,24 | 10,65 | 4 (3–7) | 7 | 11,31 | -0,46 |
| F6 (%3) | 110 | 45,5 | 28,2 | 26,4 | **0,679** | 3,18 | 10,62 | 4 (3–7) | 8 | 11,37 | -0,54 |
| F7 (en düşük) | 105 | 46,7 | 27,6 | 25,7 | **0,495** | 2,62 | 8,29 | 5 (4–7) | 7 | 9,78 | -1,29 |
| F8 (%8,5) ✔ | 108 | 45,4 | 26,9 | 27,8 | **0,692** | 3,29 | 10,77 | 5 (3–7) | 8 | 11,72 | -0,76 |
| Kabul edilenlerin hepsi birlikte: F1, F5, F8 | 103 | 46,6 | 26,2 | 27,2 | **0,718** | 3,42 | 11,19 | 4 (3–7) | 7 | 11,37 | 0,02 |

**F7 teyit gününün gecikme maliyeti** (aynı teyitli sinyaller: ertesi gün girişe karşı bir gün bekleyip giriş)

> "Hemen giriş" gerçekte yapılamaz: teyit ertesi günün kapanışında bilinir, o güne girmek geleceği bilmek olur. Bu sütun yalnızca gecikmenin maliyetini ölçmek için vardır; F7'nin kendi sonucu "gecikmeli giriş"tir.

| Teyit seviyesi | Dönem | Sinyal | Hemen giriş R | Gecikmeli giriş R | Gecikmenin etkisi (R) |
|---|---|---:|---:|---:|---:|
| en düşük | GELİŞTİRME | 105 | 0,730 | 0,495 | -0,235 |
| en düşük | TEST | 83 | -0,000 | 0,196 | 0,197 |
| orta nokta | GELİŞTİRME | 86 | 0,864 | 0,479 | -0,385 |
| orta nokta | TEST | 60 | 0,172 | -0,032 | -0,204 |
| kapanış | GELİŞTİRME | 62 | 1,073 | 0,425 | -0,648 |
| kapanış | TEST | 38 | 0,256 | -0,113 | -0,368 |

**Birleşik sonuç:** F1 (EMA 100), F5 (EMA 300), F8 (%8,5) birlikte · GELİŞTİRME farkı 0,049 R, TEST farkı 0,056 R, TEST'te 79 sinyal → üç şartı sağlıyor.

### Motordaki karşılığı

Kabul edilen filtreler `tarayici_motor.py`'de `AlimFiltreleri` ayarıyla açılıp kapatılabilir; skor ve `AL` sütunu değişmez, filtrelenmiş sinyal `AL_filtreli` sütunundadır.

- Kısa vade (günlük): filtre yok
- Orta vade (haftalık): aktif · piyasa_ema=100, uzun_trend_ema=300, tavan_esik=0.085

## Sınırlamalar

- **Hayatta kalma yanlılığı:** test evreni bugünkü BIST 100 listesidir. Geçmişte endekste olup çıkarılan, iflas eden ya da işlemden kaldırılan hisseler yoktur; endekse sonradan girenler genelde iyi performans gösterdiği için girmiştir. Sonuçlar bu yüzden olduğundan iyi görünebilir.
- Bazı hisseler borsaya 2021'den sonra girdi; GELİŞTİRME döneminde daha az hisse vardır.
- Bölünme/bedelsiz onarımında oran açılış boşluğundan tahmin edilir; hata en fazla o geceki gerçek piyasa hareketi kadardır. Limit içinde kalan küçük bedelli/bedelsizler onarılmaz.
- Gün içi fiyat sırası bilinmez: aynı barda stop ve hedef görüldüyse stop sayılır (kötümser).
- Likidite, tavan/taban kilidinde işlem yapılamaması ve açığa satış kısıtları modellenmemiştir.
- Rastgele gün kıyası her barı kullanır; ardışık günlerin işlemleri birbirinden bağımsız değildir.

