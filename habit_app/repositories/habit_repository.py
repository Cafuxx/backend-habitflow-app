"""
HabitRepository — all database operations for habits and habit logs.

Responsibilities:
  - CRUD for the `habits` table (scoped to the authenticated user).
  - Insert and aggregate rows in the `habit_logs` table.
  - Provide raw data that the service layer uses for streak / progress
    calculations.

Row-level security (RLS) is expected to be enabled on both tables in
Supabase so that a user can only read/write their own records.  The
client-side code enforces the same constraint by always filtering on
`user_id`, providing defence-in-depth.
"""

from datetime import date
from typing import List, Optional

from habit_app.models.habit import Habit
from habit_app.models.habit_log import HabitLog
from habit_app.services.supabase_service import SupabaseService


class HabitRepository:
    """
    Data-access object for the `habits` and `habit_logs` tables.
    """

    HABITS_TABLE = "habits"
    LOGS_TABLE = "habit_logs"

    # ==================================================================
    # Habit CRUD
    # ==================================================================

    def get_all_for_user(self, user_id: str) -> List[Habit]:
        """
        Fetch all active habits belonging to a user.

        Args:
            user_id: The authenticated user's UUID.

        Returns:
            A list of Habit instances, ordered by creation date.
        """
        client = SupabaseService.get_client()
        response = (
            client.table(self.HABITS_TABLE)
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at", desc=False)
            .execute()
        )
        return [Habit.from_dict(row) for row in (response.data or [])]

    def get_by_id(self, habit_id: str, user_id: str) -> Optional[Habit]:
        """
        Fetch a single habit by its primary key, scoped to the user.

        Args:
            habit_id: UUID of the habit.
            user_id: UUID of the requesting user (security scope).

        Returns:
            A Habit instance, or None if not found.
        """
        client = SupabaseService.get_client()
        response = (
            client.table(self.HABITS_TABLE)
            .select("*")
            .eq("id", habit_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if response.data:
            return Habit.from_dict(response.data)
        return None

    def create(self, habit: Habit) -> Habit:
        """
        Insert a new habit row and return the persisted instance.

        The database assigns the UUID; the returned Habit will have
        the `id` field populated.

        Args:
            habit: A Habit with id=None (not yet saved).

        Returns:
            The saved Habit with `id` populated by Supabase.

        Raises:
            RuntimeError: On API error.
        """
        client = SupabaseService.get_client()
        payload = habit.to_dict()
        payload.pop("id", None)  # Let the DB assign the UUID
        response = (
            client.table(self.HABITS_TABLE)
            .insert(payload)
            .execute()
        )
        if not response.data:
            raise RuntimeError(
                f"HabitRepository.create failed — no data returned. "
                f"Payload: {payload}"
            )
        return Habit.from_dict(response.data[0])

    def update(self, habit: Habit) -> Habit:
        """
        Update an existing habit row.

        Only mutable fields are sent to avoid overwriting server-managed
        columns such as `created_at`.

        Args:
            habit: Habit instance with a valid `id`.

        Returns:
            The updated Habit as returned by Supabase.

        Raises:
            ValueError: If habit.id is None.
        """
        if habit.id is None:
            raise ValueError("Cannot update a habit without an id.")

        client = SupabaseService.get_client()
        # Only update fields the user can change
        update_payload = {
            "name": habit.name,
            "icon": habit.icon,
            "goal_type": habit.goal_type,
            "goal_value": habit.goal_value,
            "reminder_time": (
                habit.reminder_time.strftime("%H:%M:%S")
                if habit.reminder_time
                else None
            ),
            "is_active": habit.is_active,
        }
        response = (
            client.table(self.HABITS_TABLE)
            .update(update_payload)
            .eq("id", habit.id)
            .eq("user_id", habit.user_id)  # security scope
            .execute()
        )
        if not response.data:
            raise RuntimeError(
                f"HabitRepository.update failed for id={habit.id}"
            )
        return Habit.from_dict(response.data[0])

    def soft_delete(self, habit_id: str, user_id: str) -> None:
        """
        Mark a habit as inactive (soft delete).

        Logs are preserved so that historical data is not lost.

        Args:
            habit_id: UUID of the habit to delete.
            user_id: UUID of the requesting user.
        """
        client = SupabaseService.get_client()
        client.table(self.HABITS_TABLE).update(
            {"is_active": False}
        ).eq("id", habit_id).eq("user_id", user_id).execute()

    # ==================================================================
    # Habit Log operations
    # ==================================================================

    def add_log(self, log: HabitLog) -> HabitLog:
        """
        Insert a new progress log entry.

        Args:
            log: HabitLog with id=None (not yet saved).

        Returns:
            The saved HabitLog with `id` populated.

        Raises:
            RuntimeError: On API error.
        """
        client = SupabaseService.get_client()
        payload = log.to_dict()
        payload.pop("id", None)
        response = (
            client.table(self.LOGS_TABLE)
            .insert(payload)
            .execute()
        )
        if not response.data:
            raise RuntimeError(
                f"HabitRepository.add_log failed — no data returned. "
                f"Payload: {payload}"
            )
        return HabitLog.from_dict(response.data[0])

    def get_logs_for_habit(
        self,
        habit_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[HabitLog]:
        """
        Retrieve logs for a habit, optionally filtered by date range.

        Args:
            habit_id: UUID of the parent habit.
            from_date: Inclusive start date filter (optional).
            to_date: Inclusive end date filter (optional).

        Returns:
            A list of HabitLog instances ordered by date ascending.
        """
        client = SupabaseService.get_client()
        query = (
            client.table(self.LOGS_TABLE)
            .select("*")
            .eq("habit_id", habit_id)
            .order("date", desc=False)
        )
        if from_date:
            query = query.gte("date", from_date.isoformat())
        if to_date:
            query = query.lte("date", to_date.isoformat())

        response = query.execute()
        return [HabitLog.from_dict(row) for row in (response.data or [])]

    def get_total_progress_for_date(
        self, habit_id: str, target_date: date
    ) -> float:
        """
        Sum all log values for a habit on a specific date.

        Used by the streak service to determine if the daily goal was met.

        Args:
            habit_id: UUID of the parent habit.
            target_date: The calendar date to aggregate.

        Returns:
            Total progress value (float).  Returns 0.0 if no logs exist.
        """
        logs = self.get_logs_for_habit(
            habit_id, from_date=target_date, to_date=target_date
        )
        return sum(log.value for log in logs)

    def get_distinct_completed_dates(
        self, habit_id: str, goal_value: float
    ) -> List[date]:
        """
        Return a sorted list of dates on which the habit goal was met.

        This fetches all logs and performs the aggregation in Python to
        avoid requiring a custom RPC function in Supabase.

        Args:
            habit_id: UUID of the habit.
            goal_value: The target value that constitutes a completed day.

        Returns:
            Sorted list of date objects where the sum of log values
            is >= goal_value.
        """
        logs = self.get_logs_for_habit(habit_id)

        # Aggregate values by date
        daily_totals: dict = {}
        for log in logs:
            daily_totals[log.date] = daily_totals.get(log.date, 0.0) + log.value

        # Filter to dates where the goal was reached
        completed = [d for d, total in daily_totals.items() if total >= goal_value]
        return sorted(completed)
