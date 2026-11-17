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
    "BIST 100 verileri alınırken bir ağ hatası oluştu. Lütfen internet "
    "bağlantınızı kontrol edip tekrar deneyin."
)

ERROR_NO_DATA_BATCH = "BIST 100 hisseleri için veri alınamadı."

ERROR_FX_UNAVAILABLE = (
    "USD/TL kuru verisi alınamadı. Lütfen tekrar deneyin veya TL görünümünü kullanın."
)

TAB_HISSE_DETAY = "Hisse Detay"
TAB_TARAMA = "BIST 100 Tarama"
TAB_KARSILASTIRMA = "Karşılaştırma"

EXPANDER_LABEL = "Bu ne anlama gelir?"
EXPLAIN_INDICATORS = "Göstergeler ne anlama gelir?"

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
    "bluetsman": (
        "Bluetsman Alım/Sat v2 (kısa vade, günlük grafik) alım skorunu 0-100 arasında sekiz "
        "kalemden toplar: EMA 13'ün EMA 34'ü yukarı kesmesinin tazeliği (15), fiyatın EMA 34 "
        "üzerinde olması (10), Supertrend'in yukarı yönde olması (10), RSI'ın 50-75 arasında "
        "olması (15), yükselen günde hacmin 20 günlük ortalamaya oranı (15), MACD histogramı "
        "(15), günlük hareketin ATR'ye oranı (10) ve +DI > -DI iken ADX (10). Alım sinyali için "
        "kesişim en çok 3 işlem günü önce olmalı, fiyat EMA 34 üzerinde, haftalık kapanış 20 "
        "haftalık EMA üzerinde ve skor en az 60 olmalı; her kesişime tek sinyal verilir. Stop = "
        "kapanış - 1,5 ATR, hedef = kapanış + 3 ATR (risk/ödül 2). Hesap temettü düzeltmeli "
        "günlük kapanışla yapılır."
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
HD_INDICATOR_BLUETSMAN = "Bluetsman"
HD_INDICATOR_OPTIONS = [HD_INDICATOR_BLUETSMAN, "SMA 50", "SMA 200", "EMA 20", "Bollinger"]
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
CHART_SERIES_BL_FAST = "EMA 13"
CHART_SERIES_BL_SLOW = "EMA 34"
CHART_BL_SIGNAL = "Alım sinyali"
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
# Alım sistemi (tarayici_motor: Bluetsman Alım/Sat v2)
# ---------------------------------------------------------------------------

BL_TITLE = "Bluetsman Alım Sistemi"
BL_CAPTION = (
    "Bluetsman Alım/Sat v2, kısa vade (günlük grafik); temettü düzeltmeli kapanışla. "
    "Bir sinyal taramasıdır, yatırım tavsiyesi değildir."
)
BL_STATUS_TODAY = "Bugün alım sinyali (skor {score})"
BL_STATUS_TODAY_PROVISIONAL = "Bugün ön alım sinyali (skor {score}) · kapanışta kesinleşir"
BL_STATUS_RECENT = "Son alım sinyali {days} işlem günü önce ({date}, skor {score})"
BL_STATUS_NONE = "Son {days} işlem gününde alım sinyali yok"
BL_STATUS_NO_DATA = "Alım sistemi için en az 120 işlem günü veri gerekir; tarih aralığını genişletin."
BL_GATES = (
    "Alım sinyali için: taze kesişim {cross} · fiyat > EMA 34 {price} · haftalık trend {weekly} · skor ≥ {min_score} {score}"
)
BL_SIGNAL_LEVELS = "Son sinyalin stop seviyesi {stop}, hedefi {target}."
BL_SCORE_LABEL = "Alım skoru (0-100)"
BL_TODAY = "Bugün"
BL_DAYS_AGO = "{days} gün önce"
BL_ITEM_LABELS = {
    "kesisim": "Kesişim tazeliği",
    "fiyat_ema": "Fiyat > EMA 34",
    "supertrend": "Supertrend yukarı",
    "rsi": "RSI 50-75",
    "hacim": "Hacim (yükselen gün)",
    "macd": "MACD",
    "momentum": "Momentum / ATR",
    "adx": "ADX (+DI > -DI)",
}
BL_HISTORY_TITLE = "Geçmiş alım sinyalleri (seçili tarih aralığı)"
BL_HISTORY_CAPTION = (
    "10 gün sonra: sinyal günü kapanışından 10 işlem günü sonraki kapanışa değişim "
    "(temettü düzeltmeli). Geçmiş sonuçlar gelecek için garanti değildir."
)
BL_HISTORY_EMPTY = "Seçili tarih aralığında hiç alım sinyali oluşmadı."
BL_COL_DATE = "Tarih"
BL_COL_SCORE = "Skor"
BL_COL_CLOSE = "Kapanış"
BL_COL_STOP = "Stop"
BL_COL_TARGET = "Hedef"
BL_COL_FORWARD = "10 gün sonra"
BL_HISTORY_SUMMARY = "{count} sinyal · 10 gün sonra yükselen: {up}/{done} · ortalama {avg}"

# Güncellik ve piyasa durumu
LIVE_LAST_DATA = "Son veri"
LIVE_UPDATED = "Son güncelleme"
LIVE_MARKET = "Piyasa"
LIVE_OPEN = "Açık"
LIVE_CLOSED = "Kapalı"
LIVE_REFRESH = "Şimdi yenile"
LIVE_REFRESH_WAIT = "Veri en fazla 2 dakikada bir yenilenebilir. {seconds} sn sonra tekrar deneyin."
LIVE_STALE = "Veri güncellenemedi, {minutes} dakika önceki veri gösteriliyor."
LIVE_SESSION_NOTE = "Bugünkü mum henüz kapanmadı. Sinyaller 18:10 kapanışında kesinleşir."
LIVE_SETTLING_NOTE = (
    "Seans kapandı; Yahoo verisi ~15 dakika gecikmeli olduğu için bugünkü sinyaller "
    "18:40'tan sonraki güncellemeyle kesinleşir."
)

# ---------------------------------------------------------------------------
# Sinyal Karnesi
# ---------------------------------------------------------------------------

BT_EXPANDER = "Sinyal Karnesi: RSI, MACD ve SMA sinyallerinin geçmiş performansı"
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
# BIST 100 Tarama
# ---------------------------------------------------------------------------

TS_TITLE = "Bugünün Alım Sinyalleri"
TS_CAPTION = "Son işlem gününde alım sinyali veren BIST 100 hisseleri, alım skoruna göre sıralı."
TS_PROVISIONAL_TITLE = "Ön sinyaller (seans sürüyor)"
TS_PROVISIONAL_BADGE = "Ön sinyal"
TS_NONE = "Bugün alım sinyali yok"
TS_RECENT_TITLE = "Son 5 işlem günündeki sinyaller"
TS_RECENT_NONE = "Son 5 işlem gününde de alım sinyali oluşmadı."
TS_SIGNAL_PRICE = "Sinyal fiyatı"
TS_SINCE = "sinyalden bu yana"
TS_STOP = "Stop"
TS_TARGET = "Hedef"
TS_RSI = "RSI"
TS_VOLUME = "Hacim"
TS_VOLUME_VALUE = "{ratio}×"

TR_RISING = "Yükselen"
TR_FALLING = "Düşen"
TR_SIGNAL_TODAY = "Bugün alım sinyali"
TR_SIGNAL_TODAY_SUB = "ön sinyal"
TR_SIGNAL_RECENT = "Son {days} günde sinyal"
TR_AS_OF = "{date} itibarıyla · günlük değişim önceki kapanışa göre"
TR_LIST_TITLE = "BIST 100 Hisseleri"
TR_LIST_CAPTION = "Alım skoru ve sinyal Bluetsman Alım/Sat v2'ye göredir; kalem kalem kırılımı Hisse Detay sekmesinde."
TR_LIST_META = "Skor {score} · RSI {rsi}"
TR_FILTER_LABEL = "Göster"
TR_FILTER_ALL = "Tümü"
TR_FILTER_SIGNAL = "Son {days} günde sinyal verenler"
TR_SEARCH_LABEL = "Hisse kodu veya şirket adı ara"
TR_SEARCH_PLACEHOLDER = "Örn. GARAN veya Koç"
TR_SORT_LABEL = "Sırala"
TR_SORT_OPTIONS = {
    "score_desc": "Alım skoru (yüksekten)",
    "change_desc": "Değişim (yüksekten)",
    "change_asc": "Değişim (düşükten)",
    "ticker": "Hisse (A-Z)",
}
TR_MISSING = "{count} hisse için veri alınamadı ve listeden çıkarıldı."
TR_NO_RESULTS = "Filtrelere uyan hisse yok. Arama metnini değiştirin."
TR_NO_SIGNALS = "Son {days} işlem gününde hiçbir BIST 100 hissesinde alım sinyali oluşmadı."
TR_NO_DATA = "Hiçbir hisse için veri alınamadı."
TR_COL_TICKER = "Hisse"
TR_COL_COMPANY = "Şirket"
TR_COL_PRICE = "Son Fiyat"
TR_COL_CHANGE = "Günlük Değişim"
TR_COL_SCORE = "Alım Skoru"
TR_COL_SIGNAL = "Son Sinyal"
TR_COL_RSI = "RSI"
TR_COL_VOLUME = "Hacim x"
TR_STRIP_FLAT = "{count} değişmeyen"
TR_STRIP_OF = "{count} hisse içinde"

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
BT_PRICE_LEGEND = "Fiyat (düzeltilmiş, TL)"

# ---------------------------------------------------------------------------
# Sistem Performansı (portföy testi; tools/sistem_raporu.py üretir)
# ---------------------------------------------------------------------------

TAB_PERFORMANS = "Sistem Performansı"
SP_TITLE = "Sistem Performansı"
SP_CAPTION = (
    "Sinyallerin geçmiş veriyle portföy simülasyonu: 100.000 TL, işlem başına %1 risk, en fazla "
    "6 pozisyon. Eğitim amaçlıdır, yatırım tavsiyesi değildir; geçmiş performans gelecek için garanti değildir."
)
SP_PERIOD_LABEL = "Dönem"
SP_PERIODS = {"TEST": "TEST (2025 ve sonrası)", "GELİŞTİRME": "GELİŞTİRME (2021-2024)"}
SP_EQUITY_TITLE = "Sermaye eğrisi (TL)"
SP_DRAWDOWN_TITLE = "Tepeden düşüş (%)"
SP_METRICS_TITLE = "Metrikler"
SP_COL_PORTFOLIO = "Portföy"
SP_COL_TRADES = "İşlem"
SP_COL_TOTAL = "Toplam getiri"
SP_COL_ANNUAL = "Yıllık getiri"
SP_COL_VOL = "Yıllık oynaklık"
SP_COL_SHARPE = "Sharpe"
SP_COL_SORTINO = "Sortino"
SP_COL_MAXDD = "Maks. düşüş"
SP_COL_DD_DAYS = "Düşüş süresi (gün)"
SP_COL_RATIO = "Getiri / maks. düşüş"
SP_AS_OF = "Veri sonu {data} · hesaplama {computed} · ayrıntılar ve yöntem: docs/sistem_raporu.md"
SP_MISSING = (
    "Performans verisi bulunamadı. Proje kökünde `python tools/sistem_raporu.py` çalıştırıldığında oluşur."
)
SP_NOTES = [
    "TEST dönemi, kuralların ve eşiklerin ayarlanmasında hiç kullanılmadı; asıl sonuç odur.",
    "Hisse evreni bugünkü BIST 100 listesidir (hayatta kalma yanlılığı): sonuçlar olduğundan iyi görünebilir.",
    "Sharpe ve Sortino risksiz getiri 0 ile hesaplandı; TL faizi yüksek olduğu için gerçekte daha düşüktür.",
    "XU100 fiyat endeksidir (temettü içermez); sistemler ve eşit ağırlıklı al-tut temettü düzeltmelidir.",
]
SP_NOTES_TITLE = "Okurken dikkat"
EXPLANATIONS["portfolio"] = (
    "Getiri / maksimum düşüş oranı, yıllık getirinin en büyük tepeden düşüşe bölümüdür; aynı getiriyi daha "
    "küçük düşüşle sağlayan portföy daha yüksek puan alır. Sharpe, getirinin oynaklığa oranıdır; Sortino "
    "yalnızca aşağı yönlü oynaklığı hesaba katar. Düşüş süresi, sermayenin bir önceki tepesinin altında "
    "kaldığı en uzun işlem günü sayısıdır."
)
