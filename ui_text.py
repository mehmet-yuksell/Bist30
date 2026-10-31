"""Türkçe arayüz metinleri (tek merkezden yönetim için)."""

APP_TITLE = "BIST Teknik Analiz Paneli"
APP_SUBTITLE = "Eğitim amaçlıdır, yatırım tavsiyesi değildir"
HEADER_LAST_DATA = "Son veri"
HEADER_SOURCE = "Yahoo Finance · gecikmeli"

FOOTER_SOURCE = "Veri kaynağı: Yahoo Finance (gecikmeli, gerçek zamanlı değildir)."
FOOTER_GITHUB_LABEL = "GitHub'da kaynak kod"
GITHUB_URL = "https://github.com/mehmet-yuksell/Bist30"

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

# ---------------------------------------------------------------------------
# Ortak arayüz durumları
# ---------------------------------------------------------------------------

LOADING_TEXT = "Veriler yükleniyor…"
ERROR_CARD_TITLE = "Veri şu anda alınamadı"
ERROR_CARD_HINT = "Sorun geçiciyse birkaç saniye sonra tekrar deneyebilirsiniz."
RETRY_LABEL = "Tekrar dene"

DATE_RANGE_LABEL = "Tarih aralığı"
DATE_RANGE_INCOMPLETE = "Lütfen bir başlangıç ve bitiş tarihi seçin."
DATE_RANGE_INVALID = "Başlangıç tarihi, bitiş tarihinden önce olmalıdır."

SYMBOL_PLACEHOLDER = "Örn. THYAO veya Türk Hava Yolları"
SYMBOL_HELP = "Listede Yahoo Finance'te güncel verisi bulunan {count} Borsa İstanbul hissesi yer alır."
SYMBOL_NOT_IN_LIST = "(listede yok)"

# ---------------------------------------------------------------------------
# Hisse Detay
# ---------------------------------------------------------------------------

HD_TICKER_LABEL = "Hisse (sembol veya şirket adıyla arayın)"
HD_EMPTY_TITLE = "Bir hisse seçin"
HD_EMPTY_BODY = (
    "Yukarıdaki kutuya sembol (örn. THYAO) veya şirket adı yazarak Borsa "
    "İstanbul'daki {count} hisse arasında arama yapabilirsiniz."
)
HD_VIEW_LABEL = "Grafik dönemi"
HD_VIEW_WINDOWS = {"1A": 30, "3A": 91, "6A": 182, "1Y": 365, "Tümü": None}
HD_CURRENCY_LABEL = "Para birimi"
HD_INDICATORS_LABEL = "Göstergeler"
HD_INDICATOR_OPTIONS = ["SMA 50", "SMA 200", "EMA 20", "Bollinger"]
HD_FX_ALIGN_FAILED = "USD/TL kuru bu tarih aralığı için hizalanamadı; TL görünümü kullanılıyor."

HERO_AS_OF = "{date} kapanışı · önceki kapanışa göre"
METRIC_52W_HIGH = "52 hafta en yüksek"
METRIC_52W_LOW = "52 hafta en düşük"
METRIC_PERIOD_HIGH = "Dönem en yüksek"
METRIC_PERIOD_LOW = "Dönem en düşük"
METRIC_VOLUME = "Hacim (adet)"
METRIC_RSI = "RSI (14)"

CHART_PANEL_VOLUME = "Hacim"
CHART_PANEL_RSI = "RSI (14)"
CHART_PANEL_MACD = "MACD (12, 26, 9)"
CHART_SERIES_SMA50 = "SMA 50"
CHART_SERIES_SMA200 = "SMA 200"
CHART_SERIES_EMA20 = "EMA 20"
CHART_SERIES_BOLLINGER = "Bollinger (20, 2)"
CHART_SERIES_MACD = "MACD"
CHART_SERIES_SIGNAL = "Sinyal"
CHART_SERIES_HISTOGRAM = "Histogram"
CHART_PRICE_AXIS = "Fiyat ({currency})"

SUMMARY_TITLE = "Teknik Özet"
SUMMARY_CAPTION = "Göstergelerin mevcut durumunun tarafsız bir betimlemesidir."
SUMMARY_ROW_RSI = "RSI (14)"
SUMMARY_ROW_MACD = "MACD"
SUMMARY_ROW_PRICE_MA = "Fiyat ve ortalamalar"
SUMMARY_ROW_CROSS = "50 / 200 günlük"

BADGE_RSI_OVERBOUGHT = "Aşırı alım bölgesi"
BADGE_RSI_OVERSOLD = "Aşırı satım bölgesi"
BADGE_RSI_NEUTRAL = "Nötr bölge"
BADGE_MACD_CROSS_UP = "Pozitif kesişim"
BADGE_MACD_CROSS_DOWN = "Negatif kesişim"
BADGE_MACD_ABOVE = "Sinyalin üzerinde"
BADGE_MACD_BELOW = "Sinyalin altında"
BADGE_PRICE_ABOVE_BOTH = "İki ortalamanın üzerinde"
BADGE_PRICE_BELOW_BOTH = "İki ortalamanın altında"
BADGE_PRICE_MIXED = "Ortalamalar arasında"
BADGE_GOLDEN_CROSS = "Altın kesişim"
BADGE_DEATH_CROSS = "Ölüm kesişimi"
BADGE_SMA_ABOVE = "50, 200'ün üzerinde"
BADGE_SMA_BELOW = "50, 200'ün altında"
BADGE_INSUFFICIENT = "Yetersiz veri"

# ---------------------------------------------------------------------------
# Sinyal Karnesi
# ---------------------------------------------------------------------------

BT_TITLE = "Sinyal Karnesi"
BT_CAPTION = (
    "Seçtiğiniz hissede üç basit teknik sinyalin geçmiş performansı. "
    "Sinyal gün sonunda oluşur, işlem ertesi günün açılışında gerçekleşir."
)
BT_COST_LABEL = "İşlem maliyeti (%, her yönde)"
BT_COST_HELP = "Alış ve satışta ayrı ayrı uygulanan varsayımsal komisyon/maliyet."
BT_NEED_MORE_DATA = (
    "Sinyal Karnesi için en az ~210 günlük veri gerekir (200 günlük ortalama "
    "hesaplanabilsin diye). Lütfen tarih aralığını genişletin."
)
BT_TOTAL_RETURN = "Toplam getiri"
BT_MAX_DRAWDOWN = "Maks. düşüş"
BT_NUM_TRADES = "İşlem sayısı"
BT_WIN_RATE = "Kazanç oranı"
BT_TAG_BEST = "En yüksek getiri"
BT_TAG_WORST = "En düşük getiri"
BT_TAG_BENCHMARK = "Karşılaştırma ölçütü"
BT_SAMPLE_TITLE = "Örnek sayısı yetersiz"
BT_EQUITY_TITLE = "Getiri Eğrileri Karşılaştırması"
BT_TRADES_TITLE = "İşlem Noktaları"
BT_TRADES_PICK = "Hangi stratejinin işlem noktalarını görmek istersiniz?"
BT_ENTRY = "Giriş"
BT_EXIT = "Çıkış"
BT_EQUITY_AXIS = "Başlangıç = 100"

# ---------------------------------------------------------------------------
# BIST 30 Tarama
# ---------------------------------------------------------------------------

TR_RISING = "Yükselen"
TR_FALLING = "Düşen"
TR_TOP_GAINER = "En çok yükselen"
TR_TOP_LOSER = "En çok düşen"
TR_AS_OF = "{date} itibarıyla · günlük değişim önceki kapanışa göre"
TR_HEATMAP_TITLE = "Günlük Değişim Isı Haritası"
TR_LIST_TITLE = "Hisseler"
TR_TREND_LABEL = "Trend durumu"
TR_SEARCH_LABEL = "Hisse kodu veya şirket adı ara"
TR_SEARCH_PLACEHOLDER = "Örn. GARAN veya Koç"
TR_VIEW_LABEL = "Görünüm"
TR_VIEW_LIST = "Liste"
TR_VIEW_TABLE = "Tablo"
TR_SORT_LABEL = "Sırala"
TR_SORT_OPTIONS = {
    "change_desc": "Değişim (yüksekten)",
    "change_asc": "Değişim (düşükten)",
    "ticker": "Hisse (A-Z)",
    "rsi_desc": "RSI (yüksekten)",
}
TR_MISSING = "{count} hisse için veri alınamadı ve listeden çıkarıldı."
TR_NO_RESULTS = "Filtrelere uyan hisse yok. Arama metnini veya trend filtresini değiştirin."
TR_NO_DATA = "Hiçbir hisse için veri alınamadı."
TR_COL_TICKER = "Hisse"
TR_COL_COMPANY = "Şirket"
TR_COL_PRICE = "Son Fiyat"
TR_COL_CHANGE = "Günlük Değişim"
TR_COL_RSI = "RSI"
TR_COL_TREND = "Trend"

# ---------------------------------------------------------------------------
# Karşılaştırma
# ---------------------------------------------------------------------------

KR_TICKERS_LABEL = "Hisseler (sembol veya şirket adıyla arayın)"
KR_LIMIT_HINT = "{count}/5 hisse seçili · en az 2, en fazla 5 hisse karşılaştırılabilir."
KR_NEED_TWO_TITLE = "En az 2 hisse seçin"
KR_NEED_TWO = "Karşılaştırma için yukarıdaki kutudan 2 ile 5 arasında hisse seçin."
KR_NOT_ENOUGH = "Karşılaştırma için yeterli veri alınamadı."
KR_RANK_TITLE = "Dönem Getirisi Sıralaması"
KR_RETURN_TITLE = "Normalize Edilmiş Getiri (Başlangıç = 100)"
KR_CORR_TITLE = "Korelasyon Isı Haritası"
KR_CORR_NOT_ENOUGH = "Korelasyon hesaplamak için yeterli ortak veri yok."
KR_PERIOD = "{start} – {end}"

DATE_BUTTON_LABEL = "Tarih"
TR_STRIP_FLAT = "{count} değişmeyen"
TR_STRIP_OF = "{count} hisse içinde"
BT_PRICE_LEGEND = "Fiyat (düzeltilmiş, TL)"
