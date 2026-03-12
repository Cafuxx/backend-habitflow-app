"""
StreakService — streak calculation and longest-streak tracking.

A "streak" is defined as the number of consecutive calendar days
(ending today or yesterday) on which the user met their habit's daily
goal.

Algorithm overview:
  1. Fetch all dates on which the habit goal was met (via the
     HabitRepository which aggregates per-date log sums).
  2. Build a set for O(1) date lookups.
  3. Walk backward from today, counting consecutive "hit" days until
     a miss is found.
  4. Walk the full sorted list to find the longest unbroken run.

The service is stateless; results are always recalculated from the
stored logs.  For large datasets a caching layer (e.g. Redis or a
Supabase materialized view) can be introduced without changing this
interface.

Future considerations:
  - Timezone handling: stores UTC dates; local device timezone should
    be applied when comparing to "today".  Use `date_utils.today_local`.
  - Freeze date for testing: inject a `reference_date` parameter.
"""

from datetime import date, timedelta
from typing import List, Optional

from habit_app.models.habit import Habit
from habit_app.repositories.habit_repository import HabitRepository
from habit_app.utils.date_utils import today_local


class StreakResult:
    """
    Value object returned by StreakService methods.

    Attributes:
        current_streak (int): Consecutive days completed up to and
            including today (or yesterday if today is not yet complete).
        longest_streak (int): Maximum unbroken run across all history.
        last_completed_date (date | None): Most recent date the goal
            was met, or None if no completions exist.
        is_complete_today (bool): True if today's goal has been met.
    """

    __slots__ = (
        "current_streak",
        "longest_streak",
        "last_completed_date",
        "is_complete_today",
    )

    def __init__(
        self,
        current_streak: int,
        longest_streak: int,
        last_completed_date: Optional[date],
        is_complete_today: bool,
    ) -> None:
        self.current_streak = current_streak
        self.longest_streak = longest_streak
        self.last_completed_date = last_completed_date
        self.is_complete_today = is_complete_today

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"StreakResult(current={self.current_streak}, "
            f"longest={self.longest_streak}, "
            f"today_complete={self.is_complete_today})"
        )


class StreakService:
    """
    Calculates streak statistics for a given habit.

    Attributes:
        _repo (HabitRepository): Data source for completed dates.
    """

    def __init__(self) -> None:
        self._repo = HabitRepository()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_streak(
        self,
        habit: Habit,
        reference_date: Optional[date] = None,
    ) -> StreakResult:
        """
        Calculate full streak statistics for a habit.

        Args:
            habit: The Habit whose logs will be evaluated.
            reference_date: Override "today" for testing or timezone
                adjustments.  Defaults to the device's local date.

        Returns:
            A StreakResult value object.
        """
        if habit.id is None:
            # Unsaved habit has no logs
            return StreakResult(
                current_streak=0,
                longest_streak=0,
                last_completed_date=None,
                is_complete_today=False,
            )

        today = reference_date or today_local()
        completed_dates = self._repo.get_distinct_completed_dates(
            habit.id, habit.goal_value
        )

        if not completed_dates:
            return StreakResult(
                current_streak=0,
                longest_streak=0,
                last_completed_date=None,
                is_complete_today=False,
            )

        completed_set = set(completed_dates)
        is_complete_today = today in completed_set
        last_completed = completed_dates[-1]  # sorted ascending

        current_streak = self._calculate_current_streak(
            completed_set, today
        )
        longest_streak = self._calculate_longest_streak(completed_dates)

        return StreakResult(
            current_streak=current_streak,
            longest_streak=longest_streak,
            last_completed_date=last_completed,
            is_complete_today=is_complete_today,
        )

    # ------------------------------------------------------------------
    # Algorithm helpers (private)
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_current_streak(
        completed_set: set, today: date
    ) -> int:
        """
        Count consecutive days from today (or yesterday) backward.

        The streak is not broken if today's goal has not been met yet
        (the user still has time today).  It IS broken if yesterday's
        goal was not met.

        Args:
            completed_set: Set of date objects on which the goal was met.
            today: The reference date for "today".

        Returns:
            Current streak length as an integer.
        """
        # Determine the most recent date to start counting from
        if today in completed_set:
            cursor = today
        elif (today - timedelta(days=1)) in completed_set:
            # Today not done yet but yesterday was — streak still alive
            cursor = today - timedelta(days=1)
        else:
            return 0  # Streak is broken

        streak = 0
        while cursor in completed_set:
            streak += 1
            cursor -= timedelta(days=1)

        return streak

    @staticmethod
    def _calculate_longest_streak(completed_dates: List[date]) -> int:
        """
        Find the longest unbroken consecutive run in the history.

        Args:
            completed_dates: Sorted (ascending) list of completed dates.

        Returns:
            Length of the longest streak.
        """
        if not completed_dates:
            return 0

        longest = 1
        current = 1

        for i in range(1, len(completed_dates)):
            # Two consecutive dates are exactly one day apart
            if (completed_dates[i] - completed_dates[i - 1]).days == 1:
                current += 1
                longest = max(longest, current)
            else:
                # Gap in history — reset current streak
                current = 1

        return longest
