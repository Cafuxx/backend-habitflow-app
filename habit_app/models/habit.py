"""
Habit model — represents a row in the Supabase `habits` table.

A Habit belongs to a single User and carries the full configuration
for that habit: its goal type, goal value, optional reminder time, and
display icon.
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional


# ---------------------------------------------------------------------------
# Enumerations kept as plain string constants so that they are easy to
# serialise to/from the database without importing the `enum` module on
# older Kivy Android builds.
# ---------------------------------------------------------------------------

class GoalType:
    """
    Allowed goal-counter types.  Stored as strings in the database so that
    future types can be added via a migration without code changes.
    """
    NUMBER = "number"           # Generic integer count
    MINUTES = "minutes"         # Time-based (minutes)
    HOURS = "hours"             # Time-based (hours)
    REPETITIONS = "repetitions" # Exercise reps

    ALL = (NUMBER, MINUTES, HOURS, REPETITIONS)


@dataclass
class Habit:
    """
    Represents a user-defined habit in the application.

    Attributes:
        id (str | None): UUID primary key.  None for habits not yet
            persisted to the database.
        user_id (str): Foreign key referencing the owning User.
        name (str): Human-readable habit name (e.g. "Drink water").
        icon (str): Icon identifier — either a Material Design icon name
            (used by KivyMD) or a relative path to a custom image.
        goal_type (str): One of GoalType constants — controls the unit
            label shown in the UI and streak calculation logic.
        goal_value (float): Numeric target the user wants to reach each
            day (e.g. 8 glasses, 30 minutes, 3 repetitions).
        reminder_time (time | None): Optional local time for a daily
            reminder notification.  Structure is stored now; push
            notification dispatch is a future feature.
        created_at (datetime): Timestamp of habit creation.
        is_active (bool): Soft-delete flag.  Inactive habits are hidden
            from the home screen but their logs are preserved.
    """

    user_id: str
    name: str
    icon: str = "star-outline"
    goal_type: str = GoalType.NUMBER
    goal_value: float = 1.0
    reminder_time: Optional[time] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    id: Optional[str] = None  # None until saved

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        """Validate key fields immediately after construction."""
        if self.goal_type not in GoalType.ALL:
            raise ValueError(
                f"Invalid goal_type '{self.goal_type}'. "
                f"Must be one of: {GoalType.ALL}"
            )
        if self.goal_value <= 0:
            raise ValueError("goal_value must be a positive number.")

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "Habit":
        """
        Build a Habit from a raw dictionary (e.g. Supabase API response).

        Args:
            data: Dictionary with keys matching the habits table columns.

        Returns:
            A fully initialised Habit instance.
        """
        created_raw = data.get("created_at")
        if isinstance(created_raw, str):
            created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        elif isinstance(created_raw, datetime):
            created_at = created_raw
        else:
            created_at = datetime.utcnow()

        reminder_raw = data.get("reminder_time")
        if isinstance(reminder_raw, str):
            # Stored as HH:MM or HH:MM:SS in PostgreSQL
            parts = reminder_raw.split(":")
            reminder_time = time(int(parts[0]), int(parts[1]))
        elif isinstance(reminder_raw, time):
            reminder_time = reminder_raw
        else:
            reminder_time = None

        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            name=data["name"],
            icon=data.get("icon", "star-outline"),
            goal_type=data.get("goal_type", GoalType.NUMBER),
            goal_value=float(data.get("goal_value", 1.0)),
            reminder_time=reminder_time,
            created_at=created_at,
            is_active=data.get("is_active", True),
        )

    def to_dict(self) -> dict:
        """
        Serialise the Habit to a plain dictionary for database inserts
        or REST payload construction.
        """
        payload: dict = {
            "user_id": self.user_id,
            "name": self.name,
            "icon": self.icon,
            "goal_type": self.goal_type,
            "goal_value": self.goal_value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "reminder_time": (
                self.reminder_time.strftime("%H:%M:%S")
                if self.reminder_time
                else None
            ),
        }
        if self.id is not None:
            payload["id"] = self.id
        return payload
