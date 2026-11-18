"""Türkçe arayüz metinleri (tek merkezden yönetim için)."""

APP_TITLE = "BIST Teknik Analiz Paneli"
APP_SUBTITLE = "Eğitim amaçlıdır, yatırım tavsiyesi değildir"
HEADER_LAST_DATA = "Son veri"
HEADER_SOURCE = "Yahoo Finance · gecikmeli"

FOOTER_SOURCE = "Veri kaynağı: Yahoo Finance (gecikmeli, gerçek zamanlı değildir)."
FOOTER_GITHUB_LABEL = "GitHub'da kaynak kod"
GITHUB_URL = "https://github.com/mehmet-yuksell/Bist30"
FOOTER_KVKK = (
    "KVKK: Uygulama üyelik istemez ve kişisel veri toplamaz. Takip listen yalnızca bu tarayıcıda saklanır; "
    "hesaplama için oturum boyunca sunucuya iletilir, kalıcı olarak kaydedilmez. Barındırma hizmeti "
    "(Streamlit Community Cloud) standart teknik erişim kayıtları tutabilir."
)
FOOTER_CREDIT = "Mehmet Yüksel · 2026"

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
        "Bluetsman Alım 1.2 ve Satım 1.2, TradingView'deki iki Pine göstergesinin birebir karşılığıdır; "
        "günlük vadede günlük, haftalık vadede haftalık mumlarla hesaplanır. Alım sinyali için sekiz "
        "koşulun hepsi aynı mumda sağlanmalı: EMA 13'ün EMA 34'ü yukarı kesmesi, hacmin 20 mumluk "
        "ortalamanın 1,05 katını aşması, RSI(14) > 50, momentum (kapanış farkı) > 0, MACD histogramı > 0, "
        "fiyatın EMA 34 üzerinde olması, Supertrend'in (ATR 10, çarpan 3) yukarı olması ve ADX(14) > 20. "
        "Alım skoru (0-100) her mumda bu koşulların puanlarından toplanır. Satış sinyali, Supertrend "
        "(ATR 10, çarpan 2,5) yukarıyken EMA 5'in EMA 13'ü aşağı kestiği mumda oluşur; skor RSI > 50 (10), "
        "hacim (10), 2 mumluk momentum > 0 (15), MACD histogramı > 0 (6), ADX(7) > 20 (15), kesişim (10) ve "
        "Supertrend (10) puanlarının toplamıdır. Skor 61 ve üstüyse SAT, 40-60 arasıysa KAR AL gösterilir. "
        "Fiyatlar TradingView gibi yalnızca bölünmeye göre düzeltilir (temettü düzeltmesi yok)."
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
HD_INDICATOR_OPTIONS = [HD_INDICATOR_BLUETSMAN, "EMA 5", "SMA 50", "SMA 200", "EMA 20", "Bollinger"]
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

# ---------------------------------------------------------------------------
# BIST 100 Tarama
# ---------------------------------------------------------------------------

TS_PROVISIONAL_BADGE = "Ön sinyal"
TS_SIGNAL_PRICE = "Sinyal fiyatı"
TS_SINCE = "sinyalden bu yana"
TS_RSI = "RSI"
TS_VOLUME = "Hacim"
TS_VOLUME_VALUE = "{ratio}×"

TR_RISING = "Yükselen"
TR_FALLING = "Düşen"
TR_SIGNAL_TODAY_SUB = "ön sinyal"
TR_AS_OF = "{date} itibarıyla · günlük değişim önceki kapanışa göre"
TR_LIST_TITLE = "BIST 100 Hisseleri"
TR_FILTER_LABEL = "Göster"
TR_FILTER_ALL = "Tümü"
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
TR_NO_DATA = "Hiçbir hisse için veri alınamadı."
TR_COL_TICKER = "Hisse"
TR_COL_COMPANY = "Şirket"
TR_COL_PRICE = "Son Fiyat"
TR_COL_CHANGE = "Günlük Değişim"
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
# Takip Listem
# ---------------------------------------------------------------------------

TAB_TAKIP = "Takip Listem"
TK_TITLE = "⭐ Takip Listem"
TK_CAPTION = (
    "Takip ettiğin hisseler iki vade için tek tabloda. Liste yalnızca bu tarayıcıda saklanır "
    "(başka cihaz için JSON indir/yükle). Eğitim amaçlıdır, yatırım tavsiyesi değildir."
)
TK_LOADING = "Liste tarayıcıdan yükleniyor…"
TK_ADD_TITLE = "Hisse ekle"
TK_ADD_CODE = "Hisse (listeden seç ya da kodu yaz; BIST 100 dışı da olur)"
TK_ADD_PRICE = "Alış fiyatı (isteğe bağlı)"
TK_ADD_QTY = "Adet (isteğe bağlı)"
TK_ADD_NOTE = "Not (isteğe bağlı)"
TK_ADD_BUTTON = "Ekle / güncelle"
TK_ADD_HELP = "Alış fiyatı girilen hisse \"elimde var\" sayılır; kâr/zarar ve satış kararları buna göre hesaplanır."
TK_BAD_CODE = "Geçersiz hisse kodu. 2-6 harf/rakam olmalı (örn. THYAO)."
TK_NOT_FOUND = "{kod} için Yahoo Finance'te veri bulunamadı; listeye eklenmedi."
TK_ADDED = "{kod} listeye eklendi."
TK_EMPTY = "Takip listen boş. Yukarıdan hisse ekleyebilirsin."
TK_SUMMARY_TITLE = "Karar özeti"
TK_SUMMARY_NONE = "Şu an karar özetine giren bir durum yok."
TK_TABLE_TITLE = "Liste"
TK_NO_DATA = "veri yok"
TK_HELD = "Elimde"
TK_COL_CODE = "Hisse"
TK_COL_PRICE = "Fiyat"
TK_COL_CHANGE = "Değişim"
TK_COL_PL_PCT = "K/Z %"
TK_COL_PL_TL = "K/Z TL"
TK_COL_SIGNAL = "{v} son sinyal"
TK_COL_NOTE = "Not"
TK_SIGNAL_BUY = "Alım"
TK_EDIT_TITLE = "Listeyi düzenle"
TK_EDIT_DELETE = "Sil"
TK_EDIT_SAVE = "Değişiklikleri kaydet"
TK_EDIT_SAVED = "Liste güncellendi."
TK_BACKUP_TITLE = "Yedekle / taşı"
TK_DOWNLOAD = "Listeyi indir (JSON)"
TK_UPLOAD = "Listeyi yükle (JSON)"
TK_UPLOAD_APPLY = "Yüklenen listeyi kullan (mevcut listenin yerine geçer)"
TK_UPLOAD_OK = "{n} hisselik liste yüklendi."
TK_UPLOAD_BAD = "Liste yüklenemedi: {hata}"

# ---------------------------------------------------------------------------
# Bluetsman Alım 1.2 ve Satım 1.2 (bluetsman.py, TradingView Pine kodlarının karşılığı)
# ---------------------------------------------------------------------------

VADE_LABEL = "Vade"
VADE_OPTIONS = {"kisa": "Günlük", "orta": "Haftalık"}
VADE_SHORT = {"kisa": "Günlük", "orta": "Haftalık"}
VADE_WEEK_NOTE = "Bu haftanın mumu cuma kapanışına kadar kesinleşmez; bu haftanın sinyalleri ön sinyaldir."
VADE_ONCE = {"kisa": "{days} gün önce", "orta": "{days} hafta önce"}
VADE_BUGUN = {"kisa": "Bugün", "orta": "Bu hafta"}

AL_TITLE = {"kisa": "Bugünün Alım Sinyalleri", "orta": "Bu Haftanın Alım Sinyalleri"}
AL_CAPTION = (
    "Bluetsman Alım 1.2: sekiz koşulun hepsi son mumda sağlandı (EMA 13 EMA 34'ü yukarı kesti, hacim, RSI, "
    "momentum, MACD, fiyat > EMA 34, Supertrend, ADX). Skora göre sıralı."
)
AL_NONE = {"kisa": "Bugün alım sinyali yok", "orta": "Bu hafta alım sinyali yok"}

ST_TITLE = {"kisa": "Bugünün Satış Sinyalleri", "orta": "Bu Haftanın Satış Sinyalleri"}
ST_CAPTION = (
    "Bluetsman Satım 1.2: Supertrend yukarıyken EMA 5 EMA 13'ü aşağı kesti. Skor 61 ve üstü SAT, "
    "40-60 arası KAR AL."
)
ST_NONE = {"kisa": "Bugün satış sinyali yok", "orta": "Bu hafta satış sinyali yok"}
ST_RECENT_TITLE = {"kisa": "Son 5 günün satış sinyalleri", "orta": "Son 5 haftanın satış sinyalleri"}
ST_RECENT_META = "{when} · skor {score} · sinyal fiyatı {price}"

KF_TITLE = "Kısa Vade Fırsatları"
KF_CAPTION = {
    "kisa": "Son 5 günde Alım 1.2 sinyali gelen ve o günden bu yana satış sinyali gelmeyen hisseler.",
    "orta": "Son 5 haftada Alım 1.2 sinyali gelen ve o haftadan bu yana satış sinyali gelmeyen hisseler.",
}
KF_NONE = {
    "kisa": "Son 5 günde satış sinyali gelmemiş alım sinyali yok.",
    "orta": "Son 5 haftada satış sinyali gelmemiş alım sinyali yok.",
}

SIGNAL_ADX = "ADX"
SIGNAL_SELL_SCORE = "Satış skoru"
SIGNAL_SELL_SCORE_VALUE = "{score} / 76"

TR_COL_SCORE = "{v} skor"
TR_COL_BUY = "{v} alım"
TR_COL_SELL = "{v} satış"
TR_SIGNAL_TODAY = {"kisa": "Bugün alım sinyali", "orta": "Bu hafta alım sinyali"}
TR_SELL_TODAY = {"kisa": "Bugün satış sinyali", "orta": "Bu hafta satış sinyali"}
TR_FILTER_SIGNAL = {"kisa": "Son {days} günde sinyal verenler", "orta": "Son {days} haftada sinyal verenler"}
TR_NO_SIGNALS = {
    "kisa": "Son {days} işlem gününde hiçbir BIST 100 hissesinde alım ya da satış sinyali oluşmadı.",
    "orta": "Son {days} haftada hiçbir BIST 100 hissesinde alım ya da satış sinyali oluşmadı.",
}
TR_LIST_CAPTION = (
    "Skor: Alım 1.2'nin 0-100 skoru (her mumda hesaplanır). Alım ve satış sütunları son 10 mumdaki en yeni "
    "sinyaldir. Koşul koşul ayrıntı Hisse Detay sekmesinde."
)
TR_LIST_META_VADE = "Günlük {k} · Haftalık {o} · RSI {rsi}"

BL_TITLE = "Bluetsman Alım 1.2 ve Satım 1.2"
BL_CAPTION = {
    "kisa": "TradingView'deki Pine göstergelerinin birebir karşılığı; günlük mumlar, bölünmeye göre düzeltilmiş fiyat.",
    "orta": "TradingView'deki Pine göstergelerinin birebir karşılığı; haftalık mumlar, bölünmeye göre düzeltilmiş fiyat.",
}
BL_STATUS_TODAY = {"kisa": "Bugün alım sinyali (skor {score})", "orta": "Bu hafta alım sinyali (skor {score})"}
BL_STATUS_TODAY_PROVISIONAL = "Ön alım sinyali (skor {score}) · mum kapanınca kesinleşir"
BL_STATUS_RECENT = "Son alım sinyali {when} ({date}, skor {score})"
BL_STATUS_NONE = {"kisa": "Son {days} işlem gününde alım sinyali yok", "orta": "Son {days} haftada alım sinyali yok"}
BL_STATUS_NO_DATA = "Göstergeler için yeterli veri yok (en az 60 gün ya da 40 hafta); tarih aralığını genişletin."
BL_MET = "Sinyal için sekiz koşulun hepsi gerekir: bugün {met}/{total} sağlanıyor."
BL_SCORE_LABEL = "Alım skoru (0-100)"
BL_ITEM_LABELS = {
    "ema_cross": "EMA 13 ↑ EMA 34",
    "volume": "Hacim > ort. ×1,05",
    "rsi": "RSI > 50",
    "momentum": "Momentum > 0",
    "macd": "MACD histogram > 0",
    "price_above": "Fiyat > EMA 34",
    "supertrend": "Supertrend yukarı",
    "adx": "ADX > 20",
}
ST_CARD_TITLE = "Satım 1.2"
ST_STATUS_TODAY = {"kisa": "Bugün {ad} sinyali (skor {score})", "orta": "Bu hafta {ad} sinyali (skor {score})"}
ST_STATUS_RECENT = "Son satış sinyali: {ad}, {when} ({date}, skor {score})"
ST_STATUS_NONE = {"kisa": "Son {days} işlem gününde satış sinyali yok", "orta": "Son {days} haftada satış sinyali yok"}
ST_RULE = (
    "Satış sinyali: Supertrend yukarıyken EMA 5 EMA 13'ü aşağı keser. Puanlar bugünkü koşullardır; skor "
    "61-76 SAT, 40-60 KAR AL."
)
ST_SCORE_LABEL = "Satış koşulları (en fazla 76)"
ST_ITEM_LABELS = {
    "rsi": "RSI > 50",
    "volume": "Hacim > ort. ×1,05",
    "momentum": "Momentum (2 mum) > 0",
    "macd": "MACD histogram > 0",
    "adx": "ADX (7) > 20",
    "ema_cross": "EMA 5 ↓ EMA 13",
    "trend_up": "Supertrend yukarı",
}
BL_HISTORY_TITLE = "Geçmiş sinyaller (seçili tarih aralığı)"
BL_HISTORY_SUMMARY = "{alim} alım · {kar_al} KAR AL · {sat} SAT sinyali"
BL_HISTORY_EMPTY = "Seçili tarih aralığında hiç sinyal oluşmadı."
BL_HISTORY_CAPTION = {
    "kisa": "{n} gün sonra: sinyal günü kapanışından {n} işlem günü sonraki kapanışa değişim.",
    "orta": "{n} hafta sonra: sinyal haftası kapanışından {n} hafta sonraki kapanışa değişim.",
}
BL_COL_DATE = "Tarih"
BL_COL_KIND = "Sinyal"
BL_COL_SCORE = "Skor"
BL_COL_CLOSE = "Kapanış"
BL_COL_FORWARD = {"kisa": "{n} gün sonra", "orta": "{n} hafta sonra"}
BL_KIND_LABELS = {"alim": "Alım", "kar_al": "KAR AL", "sat": "SAT"}

CHART_SERIES_BL_SELL = "EMA 5"
CHART_KAR_AL = "KAR AL"
CHART_SAT = "SAT"
HD_INDICATOR_EMA5 = "EMA 5"
HD_WEEKLY_INDICATORS = "Haftalık vadede mumlar ve göstergeler haftalıktır (SMA 50 = 50 hafta)."
KR_WEEKLY_NOTE = "Haftalık vadede getiri ve korelasyon haftalık kapanışlarla hesaplanır."

TK_SUMMARY_CAPTION = (
    "Yalnızca Alım 1.2 ve Satım 1.2 sinyallerine dayalı hatırlatmadır (son 5 mum, iki vade)."
)
TK_COL_SCORE = "{v} skor"
