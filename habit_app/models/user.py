"""
User model — represents a row in the Supabase `users` table.

Fields mirror the PostgreSQL schema exactly so that repository
methods can construct instances directly from raw Supabase responses
without additional transformation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """
    Represents an authenticated application user.

    Attributes:
        id (str): UUID primary key assigned by Supabase Auth.
        email (str): Unique email address used for authentication.
        created_at (datetime): Timestamp of account creation.
        display_name (str | None): Optional human-readable username shown
            in the UI.  Not stored in the auth schema but may be stored
            in a public profile table in future iterations.
    """

    id: str
    email: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    display_name: Optional[str] = None

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """
        Build a User from a raw dictionary (e.g. a Supabase API response).

        Args:
            data: Dictionary with keys matching the users table columns.

        Returns:
            A fully initialised User instance.
        """
        created_raw = data.get("created_at", None)
        if isinstance(created_raw, str):
            # Supabase returns ISO-8601 timestamps with trailing 'Z'
            created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        elif isinstance(created_raw, datetime):
            created_at = created_raw
        else:
            created_at = datetime.utcnow()

        return cls(
            id=data["id"],
            email=data["email"],
            created_at=created_at,
            display_name=data.get("display_name"),
        )

    def to_dict(self) -> dict:
        """
        Serialise the User to a plain dictionary suitable for JSON
        payloads or database inserts.
        """
        return {
            "id": self.id,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "display_name": self.display_name,
        }
