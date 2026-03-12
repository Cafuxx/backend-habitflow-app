"""
SupabaseService — centralised Supabase client singleton.

All repositories and services that need to communicate with the
Supabase backend obtain the client through this module.  Using a
singleton ensures that only one authenticated session is maintained
across the entire application lifecycle.

Configuration:
    Set SUPABASE_URL and SUPABASE_ANON_KEY in habit_app/utils/constants.py
    (or via environment variables in development).  Never commit real
    credentials — use a `.env` file and load them at startup.

Usage:
    from habit_app.services.supabase_service import SupabaseService

    client = SupabaseService.get_client()
    response = client.table("habits").select("*").execute()
"""

import os
from typing import Optional

# supabase-py v2 import
try:
    from supabase import create_client, Client
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "supabase-py is not installed.  Run:  pip install supabase"
    ) from exc

from habit_app.utils.constants import SUPABASE_URL, SUPABASE_ANON_KEY


class SupabaseService:
    """
    Singleton wrapper around the Supabase Python client.

    The client is lazily initialised on first access so that the module
    can be imported safely even before the configuration constants are
    available (useful for unit-testing individual components).
    """

    _client: Optional[Client] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def get_client(cls) -> Client:
        """
        Return the shared Supabase client, initialising it if necessary.

        Returns:
            A ready-to-use supabase.Client instance.

        Raises:
            ValueError: If SUPABASE_URL or SUPABASE_ANON_KEY are empty.
        """
        if cls._client is None:
            cls._client = cls._create_client()
        return cls._client

    @classmethod
    def reset(cls) -> None:
        """
        Destroy the current client instance.

        Call this during logout to clear any cached session state and
        force a fresh client on the next `get_client()` call.
        """
        cls._client = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @classmethod
    def _create_client(cls) -> Client:
        """
        Instantiate the Supabase client using configured credentials.

        Credentials are read first from runtime constants (which may
        themselves read from environment variables); this keeps secrets
        out of source control while still working in production builds
        where env vars are injected at build time.
        """
        url = os.environ.get("SUPABASE_URL", SUPABASE_URL)
        key = os.environ.get("SUPABASE_ANON_KEY", SUPABASE_ANON_KEY)

        if not url or url == "YOUR_SUPABASE_URL":
            raise ValueError(
                "SUPABASE_URL is not configured.  "
                "Set it in habit_app/utils/constants.py or as an "
                "environment variable."
            )
        if not key or key == "YOUR_SUPABASE_ANON_KEY":
            raise ValueError(
                "SUPABASE_ANON_KEY is not configured.  "
                "Set it in habit_app/utils/constants.py or as an "
                "environment variable."
            )

        return create_client(url, key)
