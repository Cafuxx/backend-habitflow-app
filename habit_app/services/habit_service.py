"""
HabitService — business logic for habit management and daily tracking.

This service is the primary entry point for any habit-related action
triggered from the UI screens.  It orchestrates calls to the
HabitRepository and exposes higher-level operations such as:

  - Creating / editing / deleting habits with validation.
  - Incrementing and decrementing daily progress.
  - Calculating today's progress percentage for a habit.
  - Resetting daily progress (intended to be called by a scheduler
    or background job at midnight).

The service is stateless; each method accepts explicit arguments and
delegates to the repository layer.  UI screens should hold a single
shared instance (or obtain one through a DI / service-locator in a
more advanced setup).
"""

from datetime import date
from typing import Dict, List, Optional, Tuple

from habit_app.models.habit import Habit, GoalType
from habit_app.models.habit_log import HabitLog
from habit_app.repositories.habit_repository import HabitRepository
from habit_app.utils.validators import is_valid_habit_name, is_valid_goal_value
from habit_app.utils.date_utils import today_local


class HabitService:
    """
    Orchestrates all habit-management and tracking logic.

    Attributes:
        _repo (HabitRepository): The underlying data-access layer.
    """

    def __init__(self) -> None:
        self._repo = HabitRepository()

    # ==================================================================
    # Habit Lifecycle (CRUD)
    # ==================================================================

    def create_habit(
        self,
        user_id: str,
        name: str,
        icon: str = "star-outline",
        goal_type: str = GoalType.NUMBER,
        goal_value: float = 1.0,
        reminder_time=None,
    ) -> Tuple[bool, str, Optional[Habit]]:
        """
        Validate input and create a new habit for a user.

        Args:
            user_id: Authenticated user's UUID.
            name: Display name for the habit.
            icon: Material Design icon name or image path.
            goal_type: One of GoalType constants.
            goal_value: Numeric daily goal (must be > 0).
            reminder_time: Optional datetime.time for reminders.

        Returns:
            Tuple of (success, message, habit_or_None).
        """
        # --- Validation ---
        valid, msg = is_valid_habit_name(name)
        if not valid:
            return False, msg, None

        valid, msg = is_valid_goal_value(goal_value)
        if not valid:
            return False, msg, None

        if goal_type not in GoalType.ALL:
            return (
                False,
                f"Invalid goal type. Choose from: {', '.join(GoalType.ALL)}",
                None,
            )

        try:
            habit = Habit(
                user_id=user_id,
                name=name.strip(),
                icon=icon,
                goal_type=goal_type,
                goal_value=float(goal_value),
                reminder_time=reminder_time,
            )
            saved = self._repo.create(habit)
            return True, "Habit created successfully!", saved
        except Exception as exc:  # noqa: BLE001
            return False, f"Failed to create habit: {exc}", None

    def update_habit(
        self,
        habit: Habit,
        name: Optional[str] = None,
        icon: Optional[str] = None,
        goal_type: Optional[str] = None,
        goal_value: Optional[float] = None,
        reminder_time=None,
    ) -> Tuple[bool, str, Optional[Habit]]:
        """
        Apply partial updates to an existing habit.

        Only the fields that are passed as non-None values are changed;
        unspecified fields retain their current values.

        Args:
            habit: The existing Habit model (must have a valid `id`).
            name: New habit name (optional).
            icon: New icon identifier (optional).
            goal_type: New goal type (optional).
            goal_value: New goal value (optional).
            reminder_time: New reminder time or None to clear it.

        Returns:
            Tuple of (success, message, updated_habit_or_None).
        """
        if name is not None:
            valid, msg = is_valid_habit_name(name)
            if not valid:
                return False, msg, None
            habit.name = name.strip()

        if icon is not None:
            habit.icon = icon

        if goal_type is not None:
            if goal_type not in GoalType.ALL:
                return False, "Invalid goal type.", None
            habit.goal_type = goal_type

        if goal_value is not None:
            valid, msg = is_valid_goal_value(goal_value)
            if not valid:
                return False, msg, None
            habit.goal_value = float(goal_value)

        # reminder_time can be explicitly set to None to clear
        habit.reminder_time = reminder_time

        try:
            updated = self._repo.update(habit)
            return True, "Habit updated successfully!", updated
        except Exception as exc:  # noqa: BLE001
            return False, f"Failed to update habit: {exc}", None

    def delete_habit(self, habit_id: str, user_id: str) -> Tuple[bool, str]:
        """
        Soft-delete a habit (marks it inactive, preserves logs).

        Args:
            habit_id: UUID of the habit to delete.
            user_id: UUID of the requesting user.

        Returns:
            Tuple of (success, message).
        """
        try:
            self._repo.soft_delete(habit_id, user_id)
            return True, "Habit deleted."
        except Exception as exc:  # noqa: BLE001
            return False, f"Failed to delete habit: {exc}"

    def get_habits_for_user(self, user_id: str) -> List[Habit]:
        """
        Return all active habits for a user.

        Args:
            user_id: Authenticated user's UUID.

        Returns:
            Ordered list of active Habit instances.
        """
        return self._repo.get_all_for_user(user_id)

    def get_habit_by_id(
        self, habit_id: str, user_id: str
    ) -> Optional[Habit]:
        """
        Retrieve a single habit by ID, scoped to the current user.

        Args:
            habit_id: UUID of the habit.
            user_id: Authenticated user's UUID (security check).

        Returns:
            Habit or None.
        """
        return self._repo.get_by_id(habit_id, user_id)

    # ==================================================================
    # Daily Progress Tracking
    # ==================================================================

    def log_progress(
        self,
        habit_id: str,
        value: float,
        target_date: Optional[date] = None,
    ) -> Tuple[bool, str, Optional[HabitLog]]:
        """
        Record a progress increment for a habit.

        Args:
            habit_id: UUID of the target habit.
            value: Amount to add to today's progress (must be > 0).
            target_date: Date to log against; defaults to today.

        Returns:
            Tuple of (success, message, saved_log_or_None).
        """
        if value <= 0:
            return False, "Progress value must be greater than zero.", None

        log_date = target_date or today_local()
        try:
            log = HabitLog(
                habit_id=habit_id,
                value=value,
                date=log_date,
            )
            saved = self._repo.add_log(log)
            return True, "Progress logged.", saved
        except Exception as exc:  # noqa: BLE001
            return False, f"Failed to log progress: {exc}", None

    def decrement_progress(
        self,
        habit_id: str,
        value: float,
        target_date: Optional[date] = None,
    ) -> Tuple[bool, str, Optional[HabitLog]]:
        """
        Record a negative progress adjustment (e.g. user over-counted).

        The adjustment is stored as a negative-value log entry so that
        the audit trail remains intact.

        Args:
            habit_id: UUID of the target habit.
            value: Positive amount to subtract (stored as negative).
            target_date: Date to adjust; defaults to today.

        Returns:
            Tuple of (success, message, saved_log_or_None).
        """
        if value <= 0:
            return False, "Decrement value must be greater than zero.", None
        return self.log_progress(habit_id, -abs(value), target_date)

    def get_today_progress(self, habit_id: str) -> float:
        """
        Return the total logged progress for a habit today.

        Args:
            habit_id: UUID of the habit.

        Returns:
            Sum of all log values for today (may be negative if
            decrements exceed increments, but is clamped to 0.0).
        """
        total = self._repo.get_total_progress_for_date(
            habit_id, today_local()
        )
        return max(total, 0.0)

    def get_progress_percentage(self, habit: Habit) -> float:
        """
        Calculate today's completion percentage for a habit.

        Args:
            habit: The Habit instance containing the goal_value.

        Returns:
            Float in the range [0.0, 100.0].
        """
        if habit.id is None or habit.goal_value <= 0:
            return 0.0
        progress = self.get_today_progress(habit.id)
        return min((progress / habit.goal_value) * 100.0, 100.0)

    def get_progress_summary(
        self, habits: List[Habit]
    ) -> Dict[str, dict]:
        """
        Build a summary dictionary for all provided habits.

        Intended for use by the HomeScreen to populate habit cards
        with a single batch of progress queries.

        Args:
            habits: List of active Habit instances.

        Returns:
            Dict keyed by habit UUID with sub-dict::

                {
                    "progress": float,      # raw logged value today
                    "percentage": float,    # 0–100
                    "is_complete": bool,    # True if goal reached
                }
        """
        summary = {}
        for habit in habits:
            if habit.id is None:
                continue
            progress = self.get_today_progress(habit.id)
            percentage = min(
                (progress / habit.goal_value) * 100.0
                if habit.goal_value > 0
                else 0.0,
                100.0,
            )
            summary[habit.id] = {
                "progress": progress,
                "percentage": percentage,
                "is_complete": progress >= habit.goal_value,
            }
        return summary
