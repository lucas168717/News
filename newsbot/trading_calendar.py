"""NYSE trading-day calendar (regular full-day holidays)."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# One-off closures not covered by the rules below (e.g. national days of mourning).
SPECIAL_CLOSURES = {
    date(2018, 12, 5),   # President G.H.W. Bush
    date(2025, 1, 9),    # President Carter
}


def _easter(year: int) -> date:
    # Anonymous Gregorian algorithm.
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    nxt = date(year + month // 12, month % 12 + 1, 1)
    last = nxt - timedelta(days=1)
    return last - timedelta(days=(last.weekday() - weekday) % 7)


def _observed(d: date) -> date:
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def nyse_holidays(year: int) -> set[date]:
    hol = {
        _nth_weekday(year, 1, 0, 3),     # Martin Luther King Jr. Day
        _nth_weekday(year, 2, 0, 3),     # Washington's Birthday
        _easter(year) - timedelta(days=2),  # Good Friday
        _last_weekday(year, 5, 0),       # Memorial Day
        _observed(date(year, 7, 4)),     # Independence Day
        _nth_weekday(year, 9, 0, 1),     # Labor Day
        _nth_weekday(year, 11, 3, 4),    # Thanksgiving
        _observed(date(year, 12, 25)),   # Christmas
    }
    # New Year's Day: when Jan 1 is a Saturday the NYSE does not close on Dec 31.
    ny = date(year, 1, 1)
    if ny.weekday() != 5:
        hol.add(_observed(ny))
    if year >= 2022:
        hol.add(_observed(date(year, 6, 19)))  # Juneteenth
    return hol


def is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and d not in nyse_holidays(d.year) and d not in SPECIAL_CLOSURES


def previous_trading_day(d: date) -> date:
    d -= timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def latest_trading_day(now: datetime) -> date:
    """Most recent trading day whose regular session has started by `now`."""
    now_et = now.astimezone(ET)
    d = now_et.date()
    if is_trading_day(d) and now_et.time() >= time(9, 30):
        return d
    return previous_trading_day(d)


def news_window(day: date) -> tuple[datetime, datetime]:
    """News for a trading day: from the prior session's close to midnight ET."""
    start = datetime.combine(previous_trading_day(day), time(16, 0), ET)
    end = datetime.combine(day + timedelta(days=1), time(0, 0), ET)
    return start, end
