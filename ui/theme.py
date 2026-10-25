"""Tasarım sistemi token'ları — CSS (ui/styles.py) ve Plotly (ui/charts.py) aynı kaynağı kullanır.

Kontrast notları (WCAG, #161A25 kart yüzeyi üzerinde):
- TEXT_1 14.4:1, TEXT_2 7.4:1, TEXT_3 5.6:1
- UP 7.9:1, DOWN_TEXT 5.5:1 (DOWN #EA3943 metin için 4.3:1 kaldığından yalnızca
  mum/çubuk gibi işaretlerde kullanılır; metinde DOWN_TEXT kullanılır)
- ACCENT üzerinde beyaz metin 4.6:1
"""

FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
FONT_URL = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"

# Yüzeyler
BG = "#0B0E14"
SURFACE_1 = "#161A25"
SURFACE_2 = "#1E2330"
BORDER = "#262C3A"
BORDER_STRONG = "#343B4D"
GRID = "#1C212C"

# Metin
TEXT_1 = "#E8EAF0"
TEXT_2 = "#A3AAB8"
TEXT_3 = "#8A92A3"

# Durum (fiyat yönü) — renge ek olarak her zaman ▲/▼ ve +/− kullanılır
UP = "#16C784"
DOWN = "#EA3943"
DOWN_TEXT = "#F0616A"
WARN = "#F0B429"

# Tek vurgu rengi
ACCENT = "#2F6FEB"
ACCENT_TEXT = "#6EA8FE"

# Isı haritası hücreleri (beyaz yazı ≥ 4.5:1 kalacak koyulukta uç değerler)
HEAT_UP = "#0F7A53"
HEAT_DOWN = "#B42E36"
HEAT_NEUTRAL = "#2A2F3B"

# Korelasyon için yön içermeyen ıraksak (diverging) çift: mavi <-> kırmızı.
# Fiyat yönü renkleri (yeşil/kırmızı) bilinçli olarak kullanılmaz; korelasyon
# "iyi/kötü" değil, nötr bir istatistiktir.
DIV_NEG = "#B4424A"
DIV_POS = "#2F6FEB"

# Kategorik seri renkleri (dataviz doğrulayıcısıyla koyu yüzeyde test edildi;
# sıra CVD ayrışması için önemlidir, karıştırmayın)
SERIES = ["#3987E5", "#D95926", "#199E70", "#C98500", "#D55181"]
BOLLINGER = "#9085E9"
MUTED_LINE = "#8A92A3"
MACD_LINE = "#D3D7E0"

# Boşluk ölçeği (px)
SPACE = {"1": 4, "2": 8, "3": 12, "4": 16, "5": 24, "6": 32}
RADIUS = {"sm": 8, "md": 12, "pill": 999}
