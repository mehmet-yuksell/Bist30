# Orijinal Bluetsman ile yeni sistemin karşılaştırması

> Eğitim amaçlıdır, yatırım tavsiyesi değildir. `python tools/bluetsman_karsilastirma.py` ile üretilir.

Orijinal Bluetsman (`bluetsman.py`, Pine Script'in birebir aktarımı) hiçbir parametresi değiştirilmeden ölçüldü: sinyal, 8 koşulun hepsinin aynı gün tuttuğu `buy_signal`. Değerlendirme yeni sistemin kısa vade AL'si ile aynı: ertesi gün açılıştan giriş, stop = kapanış − 1,5 ATR, hedef = kapanış + 3 ATR (2R), 20 iş günü zaman aşımı, %0,2 gidiş-dönüş maliyet, temettü/bölünme düzeltmeli fiyat, bugünkü BIST 100 listesi (hayatta kalma yanlılığı), hissenin ilk 120 günü sinyal sayılmaz. Ayrıntılı yöntem: `docs/sistem_raporu.md`.

Son satır bilgi içindir: orijinal panel düzeltilmemiş Yahoo fiyatıyla çalışıyordu; bedelsiz/bölünme günleri orada sahte düşüş olarak görünür.

## TEST (asıl sonuç)

| Sistem | Sinyal sayısı | Hedef % | Stop % | Beklenen getiri (R) | Standart hata | Hedefe medyan gün | XU100 aynı tarihlerde % | XU100'e göre fark % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Orijinal Bluetsman (8 koşul, buy_signal) | 105 | 31,4 | 61,9 | **-0,089** | ±0,137 | 5 | -0,50 | 0,04 |
| Yeni sistem kısa vade AL (tarayici_motor) | 350 | 30,9 | 63,4 | **-0,138** | ±0,072 | 6 | -0,38 | -0,04 |
| Rastgele gün (aynı stop/hedef/süre) | 45120 | 31,1 | 56,3 | **0,018** | ±0,007 | 8 | 0,29 | -0,05 |
| Orijinal Bluetsman, ham fiyatla (eski panelin verisi) | 112 | 29,5 | 65,2 | **-0,182** | ±0,129 | 6 | -0,51 | -0,44 |

## GELİŞTİRME

| Sistem | Sinyal sayısı | Hedef % | Stop % | Beklenen getiri (R) | Standart hata | Hedefe medyan gün | XU100 aynı tarihlerde % | XU100'e göre fark % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Orijinal Bluetsman (8 koşul, buy_signal) | 206 | 41,7 | 46,6 | **0,262** | ±0,096 | 6 | 2,00 | -0,83 |
| Yeni sistem kısa vade AL (tarayici_motor) | 578 | 45,0 | 44,8 | **0,374** | ±0,061 | 8 | 2,02 | -0,13 |
| Rastgele gün (aynı stop/hedef/süre) | 84298 | 39,4 | 47,8 | **0,247** | ±0,006 | 8 | 1,30 | 0,47 |
| Orijinal Bluetsman, ham fiyatla (eski panelin verisi) | 196 | 43,4 | 44,9 | **0,345** | ±0,102 | 6 | 2,23 | -0,81 |

