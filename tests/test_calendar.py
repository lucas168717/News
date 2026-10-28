from datetime import date, datetime

from newsbot.trading_calendar import ET, is_trading_day, latest_trading_day, news_window, nyse_holidays


def test_2026_holidays():
    assert nyse_holidays(2026) == {
        date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16), date(2026, 4, 3), date(2026, 5, 25),
        date(2026, 6, 19), date(2026, 7, 3), date(2026, 9, 7), date(2026, 11, 26), date(2026, 12, 25),
    }


def test_observed_rules():
    assert not is_trading_day(date(2027, 12, 24))  # Christmas on Saturday
    assert not is_trading_day(date(2027, 7, 5))    # July 4 on Sunday
    assert is_trading_day(date(2021, 12, 31))      # New Year's 2022 on Saturday: no Friday closure
    assert not is_trading_day(date(2025, 1, 9))    # special closure


def test_latest_trading_day():
    assert latest_trading_day(datetime(2026, 10, 27, 18, 15, tzinfo=ET)) == date(2026, 10, 27)
    assert latest_trading_day(datetime(2026, 10, 27, 8, 0, tzinfo=ET)) == date(2026, 10, 26)
    assert latest_trading_day(datetime(2026, 11, 1, 12, 0, tzinfo=ET)) == date(2026, 10, 30)  # Sunday
    assert latest_trading_day(datetime(2026, 11, 26, 18, 0, tzinfo=ET)) == date(2026, 11, 25)  # Thanksgiving


def test_window_spans_weekend():
    start, end = news_window(date(2026, 10, 26))  # Monday
    assert start == datetime(2026, 10, 23, 16, 0, tzinfo=ET)
    assert end == datetime(2026, 10, 27, 0, 0, tzinfo=ET)
