"""Türkçe arayüz metinleri (tek merkezden yönetim için)."""

APP_TITLE = "BIST 30 Teknik Analiz Paneli"

DISCLAIMER = (
    "Yatırım tavsiyesi değildir. Veriler Yahoo Finance üzerinden alınır ve "
    "gecikmeli olabilir. Eğitim amaçlı bir projedir."
)

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
}
