"""Borsa İstanbul seans saati ve önbellek zaman dilimi (Europe/Istanbul).

Seans hafta içi 10:00-18:10 arasıdır. Yahoo Finance BIST verisini ~15 dakika gecikmeyle
verdiği için kapanış mumu ancak 18:25 civarında oturur; bu yüzden veri 18:40'a kadar
15 dakikada bir yenilenir, sonra bir sonraki seans açılışına kadar aynı kalır.

Resmî tatiller ayrıca tutulmaz: son verinin tarihi bugün değilse piyasa kapalı sayılır.
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Istanbul")
SESSION_OPEN = time(10, 0)
SESSION_CLOSE = time(18, 10)
DATA_SETTLED = time(18, 40)  # gecikmeli kapanış verisinin oturduğu saat
REFRESH_MINUTES = 15


def now() -> datetime:
    return datetime.now(TZ)


def _is_weekday(moment: datetime) -> bool:
    return moment.weekday() < 5


def in_session(moment: datetime) -> bool:
    """Saat olarak seans içinde mi (tatilleri bilmez)."""
    return _is_weekday(moment) and SESSION_OPEN <= moment.time() < SESSION_CLOSE


def _in_refresh_window(moment: datetime) -> bool:
    return _is_weekday(moment) and SESSION_OPEN <= moment.time() < DATA_SETTLED


def next_open(moment: datetime) -> datetime:
    """`moment`ten sonraki ilk seans açılışı (hafta sonunu atlar)."""
    day = moment.date()
    if moment.time() >= SESSION_OPEN:
        day += timedelta(days=1)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return datetime.combine(day, SESSION_OPEN, tzinfo=TZ)


def cache_slot(moment: datetime) -> str:
    """Önbellek anahtarı: seansta 15 dakikalık blok, seans dışında bir sonraki açılış.

    Anahtar değişince veri yeniden çekilir; seans dışında anahtar açılışa kadar aynı kalır.
    """
    if _in_refresh_window(moment):
        minutes = (moment.hour * 60 + moment.minute) - (SESSION_OPEN.hour * 60 + SESSION_OPEN.minute)
        return f"{moment.date().isoformat()}#{minutes // REFRESH_MINUTES}"
    return f"kapali→{next_open(moment).isoformat()}"


def market_open(moment: datetime, last_data_date: date | None) -> bool:
    """Piyasa açık mı: seans saati ve son veri bugüne ait (tatilde veri gelmez)."""
    return in_session(moment) and last_data_date == moment.date()


def provisional(moment: datetime, last_data_date: date | None) -> bool:
    """Bugünkü mum henüz kesin değil mi (seans sürüyor ya da kapanış verisi oturmadı)."""
    return last_data_date == moment.date() and _in_refresh_window(moment)
