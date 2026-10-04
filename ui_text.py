"""Türkçe arayüz metinleri (tek merkezden yönetim için)."""

APP_TITLE = "BIST 30 Teknik Analiz Paneli"

DISCLAIMER = (
    "Yatırım tavsiyesi değildir. Veriler Yahoo Finance üzerinden alınır ve "
    "gecikmeli olabilir. Eğitim amaçlı bir projedir."
)

FOOTER_CREDIT = "Mehmet Yüksel © 2026"

ERROR_NETWORK = (
    "{ticker} için veri alınırken bir ağ hatası oluştu. Lütfen internet "
    "bağlantınızı kontrol edip tekrar deneyin."
)

ERROR_NO_DATA = (
    "{ticker} için seçilen tarih aralığında veri bulunamadı. Hisse kodunu "
    "veya tarih aralığını değiştirip tekrar deneyin."
)

ERROR_INCOMPLETE_DATA = (
    "{ticker} için veri eksik görünüyor. Lütfen daha sonra tekrar deneyin."
)

ERROR_NETWORK_BATCH = (
    "BIST 30 verileri alınırken bir ağ hatası oluştu. Lütfen internet "
    "bağlantınızı kontrol edip tekrar deneyin."
)

ERROR_NO_DATA_BATCH = "BIST 30 hisseleri için veri alınamadı."

ERROR_FX_UNAVAILABLE = (
    "USD/TL kuru verisi alınamadı. Lütfen tekrar deneyin veya TL görünümünü kullanın."
)

TAB_HISSE_DETAY = "Hisse Detay"
TAB_TARAMA = "BIST 30 Tarama"
TAB_KARSILASTIRMA = "Karşılaştırma"

EXPANDER_LABEL = "Bu ne anlama gelir?"

EXPLANATIONS = {
    "sma_ema": (
        "SMA (Basit Hareketli Ortalama) ve EMA (Üssel Hareketli Ortalama), "
        "fiyatın belirli bir dönemdeki ortalamasını göstererek günlük "
        "dalgalanmaları yumuşatır. EMA, son fiyatlara daha fazla ağırlık "
        "verdiği için değişimlere SMA'dan daha hızlı tepki verir."
    ),
    "bollinger": (
        "Bollinger Bantları, fiyatın hareketli ortalaması etrafına, son "
        "dönemdeki oynaklığa (standart sapma) göre çizilen üst ve alt "
        "sınırlardır. Bantların daralması düşük oynaklığı, genişlemesi "
        "yüksek oynaklığı gösterir."
    ),
    "rsi": (
        "RSI (Göreceli Güç Endeksi), fiyat hareketinin hızını 0-100 "
        "arasında ölçer. Geleneksel olarak 70 üzeri 'aşırı alım', 30 altı "
        "'aşırı satım' bölgesi olarak yorumlanır. Tek başına bir sinyal "
        "değildir, diğer göstergelerle birlikte değerlendirilir."
    ),
    "macd": (
        "MACD, iki farklı hızdaki üssel hareketli ortalamanın (EMA) "
        "farkını gösterir. MACD çizgisinin kendi ortalaması olan sinyal "
        "çizgisinin üzerine çıkıp altına inmesi, momentumdaki değişimleri "
        "yansıtır."
    ),
    "golden_death_cross": (
        "Altın kesişim, kısa dönemli ortalamanın (50 günlük) uzun dönemli "
        "ortalamanın (200 günlük) üzerine çıkmasıdır; ölüm kesişimi ise "
        "tersidir. Bunlar gecikmeli göstergelerdir, her zaman doğru sonuç "
        "vermeyebilir."
    ),
    "normalized_return": (
        "Normalize edilmiş getiri, farklı fiyat seviyelerindeki hisselerin "
        "performansını adil şekilde karşılaştırabilmek için her hissenin "
        "başlangıç fiyatını 100 kabul ederek yeniden ölçeklendirir."
    ),
    "correlation": (
        "Korelasyon katsayısı, iki hissenin günlük getirilerinin birlikte "
        "hareket etme derecesini -1 ile +1 arasında ölçer. +1'e yakın "
        "değerler aynı yönde, -1'e yakın değerler ters yönde hareketi "
        "gösterir; 0'a yakın değerler aralarında belirgin bir doğrusal "
        "ilişki olmadığını gösterir. Geçmiş korelasyon, gelecekte aynı "
        "kalacağının garantisi değildir."
    ),
    "backtest": (
        "Sinyal Karnesi, seçtiğiniz hissede üç basit teknik sinyalin geçmişte "
        "nasıl performans gösterdiğini gösterir. Sinyal bir günün kapanışında "
        "oluşur, işlem ERTESİ GÜNÜN açılışında gerçekleştirilir (ileriye bakış "
        "hatası yoktur). Parametreler (RSI 14/30/70, MACD 12/26/9, SMA 50/200) "
        "sabittir; bu hisseye özel olarak optimize edilmemiştir."
    ),
    "usd_view": (
        "Türk Lirası yüksek enflasyon ve kur hareketleri nedeniyle zaman "
        "içinde değer kaybedebilir; bu da TL bazlı bir grafikte fiyatın "
        "'yükseliyor' görünmesine ama aslında dolar bazında aynı kaldığına "
        "ya da gerilediğine yol açabilir. Dolar bazında bakmak, kur "
        "etkisinden arındırılmış, uluslararası yatırımcıların gördüğüne "
        "daha yakın bir performans resmi verir."
    ),
}

BACKTEST_DISCLAIMER = (
    "Geçmiş performans gelecek için garanti değildir. Basitleştirilmiş bir "
    "modeldir; vergi, kayma (slippage) ve likidite dikkate alınmamıştır."
)

BACKTEST_INSUFFICIENT_SAMPLE = (
    "{name}: örnek sayısı yetersiz ({count} işlem), sonuç güvenilir değildir."
)
