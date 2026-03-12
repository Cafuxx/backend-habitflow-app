"""
validators — input validation functions used across layers.

All validators return a (bool, str) tuple:
  - (True,  "")          — valid input
  - (False, "message")   — invalid, message explains why

This pattern allows UI screens to display the error message inline
without coupling the validation logic to any specific widget.
"""

import re
from typing import Tuple

from habit_app.utils.constants import (
    HABIT_NAME_MIN_LENGTH,
    HABIT_NAME_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
    GOAL_VALUE_MAX,
)

# Pre-compile the email regex for performance (called on every keystroke)
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+$"
)


# ---------------------------------------------------------------------------
# Authentication validators
# ---------------------------------------------------------------------------

def is_valid_email(email: str) -> bool:
    """
    Return True if `email` is a syntactically valid email address.

    This is a lightweight format check only — it does not verify that
    the mailbox exists.  Supabase will perform its own validation on
    sign-up.

    Args:
        email: The email string to validate.

    Returns:
        True if the format is acceptable, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False
    return bool(_EMAIL_RE.match(email.strip()))


def is_valid_password(password: str) -> Tuple[bool, str]:
    """
    Validate a plain-text password against the application's requirements.

    Rules:
      - Between PASSWORD_MIN_LENGTH and PASSWORD_MAX_LENGTH characters.
      - Must contain at least one letter and one number.

    Args:
        password: The password string to validate.

    Returns:
        (True, "") if valid; (False, error_message) otherwise.
    """
    if not password:
        return False, "Password cannot be empty."

    length = len(password)
    if length < PASSWORD_MIN_LENGTH:
        return (
            False,
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters.",
        )
    if length > PASSWORD_MAX_LENGTH:
        return (
            False,
            f"Password must not exceed {PASSWORD_MAX_LENGTH} characters.",
        )
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."

    return True, ""


# ---------------------------------------------------------------------------
# Habit validators
# ---------------------------------------------------------------------------

def is_valid_habit_name(name: str) -> Tuple[bool, str]:
    """
    Validate a habit display name.

    Rules:
      - Between HABIT_NAME_MIN_LENGTH and HABIT_NAME_MAX_LENGTH characters
        after stripping leading/trailing whitespace.
      - No leading or trailing whitespace in the stored value.
      - Must not be blank.

    Args:
        name: The raw habit name string from the UI input field.

    Returns:
        (True, "") if valid; (False, error_message) otherwise.
    """
    if not name or not isinstance(name, str):
        return False, "Habit name cannot be empty."

    stripped = name.strip()
    if len(stripped) < HABIT_NAME_MIN_LENGTH:
        return (
            False,
            f"Habit name must be at least {HABIT_NAME_MIN_LENGTH} characters.",
        )
    if len(stripped) > HABIT_NAME_MAX_LENGTH:
        return (
            False,
            f"Habit name must not exceed {HABIT_NAME_MAX_LENGTH} characters.",
        )
    return True, ""


def is_valid_goal_value(value) -> Tuple[bool, str]:
    """
    Validate a habit goal value.

    Rules:
      - Must be convertible to float.
      - Must be strictly greater than 0.
      - Must not exceed GOAL_VALUE_MAX.

    Args:
        value: The raw value from the UI input (may be str or numeric).

    Returns:
        (True, "") if valid; (False, error_message) otherwise.
    """
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False, "Goal value must be a number."

    if numeric <= 0:
        return False, "Goal value must be greater than zero."
    if numeric > GOAL_VALUE_MAX:
        return (
            False,
            f"Goal value must not exceed {int(GOAL_VALUE_MAX):,}.",
        )
    return True, ""


def is_valid_reminder_time_string(time_str: str) -> Tuple[bool, str]:
    """
    Validate a time string intended for reminderTime storage.

    Accepts formats: "HH:MM" or "HH:MM:SS".

    Args:
        time_str: Time string from a time-picker widget.

    Returns:
        (True, "") if valid; (False, error_message) otherwise.
    """
    if not time_str:
        # No reminder is a valid state
        return True, ""

    pattern = re.compile(r"^\d{2}:\d{2}(:\d{2})?$")
    if not pattern.match(time_str):
        return False, "Invalid time format. Expected HH:MM."

    parts = time_str.split(":")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23):
        return False, "Hour must be between 0 and 23."
    if not (0 <= minute <= 59):
        return False, "Minute must be between 0 and 59."

    return True, ""
