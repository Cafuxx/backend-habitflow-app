"""
date_utils — shared date and time helper functions.

Centralising date operations in one module makes it straightforward
to swap out implementations (e.g. for timezone handling or test mocking)
without touching every caller.
"""

from datetime import date, datetime, timezone


def today_local() -> date:
    """
    Return the current local calendar date on the device.

    Prefer this over `datetime.today().date()` so that timezone logic
    is managed in one place.  On Android/iOS the system timezone is
    respected automatically by Python's `datetime` module.

    Returns:
        Current local date as a `datetime.date` object.
    """
    return datetime.now().date()


def today_utc() -> date:
    """
    Return the current UTC calendar date.

    Use this when comparing against dates stored in a UTC-normalised
    database column.

    Returns:
        Current UTC date as a `datetime.date` object.
    """
    return datetime.now(timezone.utc).date()


def now_utc() -> datetime:
    """
    Return the current UTC datetime with timezone info attached.

    Always prefer this over `datetime.utcnow()` (which is naive) when
    you need a timezone-aware timestamp for API payloads.

    Returns:
        Timezone-aware UTC datetime.
    """
    return datetime.now(timezone.utc)


def format_date_display(d: date) -> str:
    """
    Format a date for human-readable display in the UI.

    Examples:
        format_date_display(date(2025, 1, 5))  →  "Jan 5, 2025"

    Args:
        d: The date to format.

    Returns:
        A localised-style date string.
    """
    return d.strftime("%b %-d, %Y") if hasattr(d, "strftime") else str(d)


def format_date_short(d: date) -> str:
    """
    Format a date as a compact string for streak calendars.

    Examples:
        format_date_short(date(2025, 1, 5))  →  "05 Jan"

    Args:
        d: The date to format.

    Returns:
        Short date string.
    """
    return d.strftime("%d %b")


def days_since(d: date) -> int:
    """
    Return the number of days between a past date and today.

    Args:
        d: The past date.

    Returns:
        Non-negative integer number of days.  Returns 0 if `d` is today
        or in the future.
    """
    delta = today_local() - d
    return max(delta.days, 0)


def is_today(d: date) -> bool:
    """
    Return True if the given date is today (local).

    Args:
        d: Date to check.
    """
    return d == today_local()


def is_yesterday(d: date) -> bool:
    """
    Return True if the given date is yesterday (local).

    Args:
        d: Date to check.
    """
    from datetime import timedelta
    return d == today_local() - timedelta(days=1)
