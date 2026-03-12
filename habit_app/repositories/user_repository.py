"""
UserRepository — all database operations that concern the user profile.

Responsibilities:
  - Fetch a user's profile record from the `users` table.
  - Upsert a profile row after a successful Supabase Auth sign-up.

The repository does NOT handle authentication (that belongs to
AuthService).  It operates purely on the public `users` table which
mirrors basic profile data next to the Supabase Auth user record.

Note on table design:
  Supabase Auth stores core credentials in `auth.users` (managed
  internally).  We maintain a parallel `public.users` table with
  display_name and any future profile fields.  A PostgreSQL trigger
  can auto-insert a row into `public.users` on auth signup; this
  repository upserts that row from the client side as a fallback.
"""

from typing import Optional

from habit_app.models.user import User
from habit_app.services.supabase_service import SupabaseService


class UserRepository:
    """
    Data-access object for the `users` table.

    All methods interact exclusively with the Supabase REST API through
    the shared client singleton; no raw SQL is written here.
    """

    TABLE = "users"

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user profile by primary key.

        Args:
            user_id: The UUID of the user (matches Supabase Auth uid).

        Returns:
            A User instance if found, otherwise None.
        """
        client = SupabaseService.get_client()
        response = (
            client.table(self.TABLE)
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        if response.data:
            return User.from_dict(response.data)
        return None

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user profile by email address.

        Args:
            email: The email to look up.

        Returns:
            A User instance if found, otherwise None.
        """
        client = SupabaseService.get_client()
        response = (
            client.table(self.TABLE)
            .select("*")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
        if response.data:
            return User.from_dict(response.data)
        return None

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def upsert(self, user: User) -> User:
        """
        Insert or update a user profile row.

        Uses `upsert` so that it is safe to call after both sign-up
        (creates a new row) and profile updates (overwrites existing).

        Args:
            user: The User model to persist.

        Returns:
            The updated User instance (with any server-side defaults
            applied, such as `created_at`).

        Raises:
            RuntimeError: If the Supabase API returns an error.
        """
        client = SupabaseService.get_client()
        payload = user.to_dict()
        response = (
            client.table(self.TABLE)
            .upsert(payload)
            .execute()
        )
        if not response.data:
            raise RuntimeError(
                f"UserRepository.upsert failed — no data returned. "
                f"Payload: {payload}"
            )
        return User.from_dict(response.data[0])

    def update_display_name(self, user_id: str, display_name: str) -> None:
        """
        Update only the display_name field for a given user.

        Args:
            user_id: Target user's UUID.
            display_name: New display name string.
        """
        client = SupabaseService.get_client()
        client.table(self.TABLE).update(
            {"display_name": display_name}
        ).eq("id", user_id).execute()
