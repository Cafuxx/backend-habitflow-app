"""
HabitLog model — represents a row in the Supabase `habit_logs` table.

Each HabitLog records the progress a user made toward a habit goal on
a particular calendar date.  Multiple logs per habit per day are
allowed (incremental updates), but the streak calculation service
aggregates them before comparison.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class HabitLog:
    """
    Represents one progress entry for a habit on a specific date.

    Attributes:
        habit_id (str): Foreign key to the Habit this log belongs to.
        value (float): The amount of progress recorded in this entry.
            The unit is determined by the parent Habit's `goal_type`.
        date (date): The calendar date for which this log applies.
        id (str | None): UUID primary key.  None if not yet persisted.
        created_at (datetime): Wall-clock timestamp of when the log was
            inserted (useful for ordering multiple logs on the same day).
    """

    habit_id: str
    value: float
    date: date = field(default_factory=date.today)
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "HabitLog":
        """
        Build a HabitLog from a raw dictionary (e.g. Supabase response).

        Args:
            data: Dictionary with keys matching the habit_logs columns.

        Returns:
            A fully initialised HabitLog instance.
        """
        # Parse the date field — Supabase returns ISO date strings
        date_raw = data.get("date")
        if isinstance(date_raw, str):
            log_date = date.fromisoformat(date_raw)
        elif isinstance(date_raw, date):
            log_date = date_raw
        else:
            log_date = date.today()

        created_raw = data.get("created_at")
        if isinstance(created_raw, str):
            created_at = datetime.fromisoformat(
                created_raw.replace("Z", "+00:00")
            )
        elif isinstance(created_raw, datetime):
            created_at = created_raw
        else:
            created_at = datetime.utcnow()

        return cls(
            id=data.get("id"),
            habit_id=data["habit_id"],
            value=float(data.get("value", 0.0)),
            date=log_date,
            created_at=created_at,
        )

    def to_dict(self) -> dict:
        """
        Serialise the HabitLog to a plain dictionary for database inserts
        or REST payload construction.
        """
        payload: dict = {
            "habit_id": self.habit_id,
            "value": self.value,
            "date": self.date.isoformat(),
            "created_at": self.created_at.isoformat(),
        }
        if self.id is not None:
            payload["id"] = self.id
        return payload
