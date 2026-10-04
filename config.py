# BIST 30 hisse listesi ve genel ayarlar.
#
# BIST30_TICKERS burada BIST kodu -> şirket adı eşlemesi olarak tutulur (Yahoo Finance
# sonekı ".IS" olmadan). Yahoo Finance üzerinden veri çekerken data.py bu sonekı ekler.
#
# Liste, Borsa İstanbul'un 1 Ekim 2026 itibarıyla geçerli çeyreklik endeks revizyonuyla
# (KAP bildirimi: Destek Finans Faktoring/DSTKF çıkarıldı, TR Anadolu Metal Madencilik/TRMET
# dahil edildi) güncellenmiş haline göre doğrulanmıştır. BIST 30 bileşenleri üç ayda bir
# değişebilir; bu listeyi periyodik olarak borsaistanbul.com veya KAP üzerinden kontrol edin.

BIST30_LAST_UPDATED = "2026-10-04"

BIST30_TICKERS: dict[str, str] = {
    "AEFES": "Anadolu Efes",
    "AKBNK": "Akbank",
    "ASELS": "Aselsan",
    "ASTOR": "Astor Enerji",
    "BIMAS": "BİM Birleşik Mağazalar",
    "EKGYO": "Emlak Konut GYO",
    "ENKAI": "Enka İnşaat",
    "EREGL": "Ereğli Demir Çelik",
    "FROTO": "Ford Otosan",
    "GARAN": "Garanti BBVA",
    "GUBRF": "Gübre Fabrikaları",
    "ISCTR": "Türkiye İş Bankası (C)",
    "KCHOL": "Koç Holding",
    "KRDMD": "Kardemir (D)",
    "MGROS": "Migros",
    "PETKM": "Petkim",
    "PGSUS": "Pegasus",
    "SAHOL": "Sabancı Holding",
    "SASA": "Sasa Polyester",
    "SISE": "Şişecam",
    "TAVHL": "TAV Havalimanları",
    "TCELL": "Turkcell",
    "THYAO": "Türk Hava Yolları",
    "TOASO": "Tofaş Otomobil Fabrikası",
    "TRALT": "Türk Altın İşletmeleri",
    "TRMET": "TR Anadolu Metal Madencilik",
    "TTKOM": "Türk Telekom",
    "TUPRS": "Tüpraş",
    "VAKBN": "VakıfBank",
    "YKBNK": "Yapı Kredi Bankası",
}

YAHOO_SUFFIX = ".IS"
