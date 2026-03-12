"""
AuthService — authentication business logic.

Wraps Supabase Auth operations (sign-up, sign-in, sign-out, session
refresh) and exposes a clean interface to the UI screens.

Session persistence:
    Supabase-py v2 stores the JWT in memory by default.  For a mobile
    app we persist the session token to a local JSON file so that users
    remain logged in between app restarts.  The token file is stored in
    a platform-appropriate location (see _get_session_path).

Security notes:
    - Passwords are NEVER stored locally; only the JWT is persisted.
    - The session file path is inside the app's private data directory
      on Android/iOS, which is not accessible to other apps.
    - Tokens are automatically refreshed by supabase-py when possible.
"""

import json
import os
from typing import Optional, Tuple

from habit_app.models.user import User
from habit_app.repositories.user_repository import UserRepository
from habit_app.services.supabase_service import SupabaseService
from habit_app.utils.validators import is_valid_email, is_valid_password


# ---------------------------------------------------------------------------
# Session file path helper
# ---------------------------------------------------------------------------

def _get_session_path() -> str:
    """
    Return the absolute path for the local session cache file.

    On Android the Kivy environment exposes `ANDROID_PRIVATE` which
    points to the app's private storage.  On desktop / iOS we fall
    back to a `.habitflow` directory in the user's home folder.
    """
    android_private = os.environ.get("ANDROID_PRIVATE")
    if android_private:
        return os.path.join(android_private, "session.json")
    base = os.path.expanduser("~")
    folder = os.path.join(base, ".habitflow")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "session.json")


SESSION_FILE = _get_session_path()


class AuthService:
    """
    Handles all user authentication flows.

    Attributes:
        _current_user (User | None): The currently authenticated user,
            kept in memory for fast access after login.
        _user_repo (UserRepository): Repository for syncing the public
            user profile row after authentication events.
    """

    def __init__(self) -> None:
        self._current_user: Optional[User] = None
        self._user_repo = UserRepository()

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def current_user(self) -> Optional[User]:
        """Return the currently signed-in user, or None."""
        return self._current_user

    @property
    def is_authenticated(self) -> bool:
        """Return True if a user session is active."""
        return self._current_user is not None

    # ------------------------------------------------------------------
    # Sign-up
    # ------------------------------------------------------------------

    def sign_up(
        self, email: str, password: str
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user with Supabase Auth.

        After a successful auth sign-up we upsert a row in the public
        `users` table so that profile queries work immediately.

        Args:
            email: The new user's email address.
            password: Plain-text password (min 6 characters).

        Returns:
            Tuple of (success: bool, message: str, user: User | None).
            On failure, user is None and message describes the error.
        """
        # --- Input validation (client-side) ---
        if not is_valid_email(email):
            return False, "Please enter a valid email address.", None
        ok, msg = is_valid_password(password)
        if not ok:
            return False, msg, None

        try:
            client = SupabaseService.get_client()
            response = client.auth.sign_up(
                {"email": email, "password": password}
            )

            if response.user is None:
                return (
                    False,
                    "Sign-up failed.  Please check your email and try again.",
                    None,
                )

            # Build and persist the public profile row
            user = User(
                id=response.user.id,
                email=response.user.email,
            )
            self._user_repo.upsert(user)

            # Persist session locally
            if response.session:
                self._save_session(response.session)

            self._current_user = user
            return True, "Account created successfully!", user

        except Exception as exc:  # noqa: BLE001
            return False, f"Sign-up error: {exc}", None

    # ------------------------------------------------------------------
    # Sign-in
    # ------------------------------------------------------------------

    def sign_in(
        self, email: str, password: str
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Sign in an existing user with email and password.

        Args:
            email: Registered email address.
            password: Plain-text password.

        Returns:
            Tuple of (success: bool, message: str, user: User | None).
        """
        if not is_valid_email(email):
            return False, "Please enter a valid email address.", None

        try:
            client = SupabaseService.get_client()
            response = client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if response.user is None:
                return False, "Invalid email or password.", None

            # Fetch or create the public profile
            user = self._user_repo.get_by_id(response.user.id)
            if user is None:
                # Profile row may be missing — upsert it
                user = User(id=response.user.id, email=response.user.email)
                self._user_repo.upsert(user)

            # Persist session and set in-memory reference
            if response.session:
                self._save_session(response.session)

            self._current_user = user
            return True, "Welcome back!", user

        except Exception as exc:  # noqa: BLE001
            return False, f"Login error: {exc}", None

    # ------------------------------------------------------------------
    # Sign-out
    # ------------------------------------------------------------------

    def sign_out(self) -> None:
        """
        Sign out the current user and clear all local session data.

        Resets the Supabase client singleton so the next operation
        starts with a clean, unauthenticated client.
        """
        try:
            client = SupabaseService.get_client()
            client.auth.sign_out()
        except Exception:  # noqa: BLE001
            pass  # Best-effort; we clear state regardless

        self._current_user = None
        self._delete_session()
        SupabaseService.reset()

    # ------------------------------------------------------------------
    # Session restore (app startup)
    # ------------------------------------------------------------------

    def restore_session(self) -> bool:
        """
        Attempt to restore a previously saved session from disk.

        Call this at app startup before showing login/home screen to
        implement persistent login.

        Returns:
            True if a valid session was restored, False otherwise.
        """
        session_data = self._load_session()
        if not session_data:
            return False

        try:
            client = SupabaseService.get_client()
            # Provide saved tokens to the client
            response = client.auth.set_session(
                access_token=session_data["access_token"],
                refresh_token=session_data["refresh_token"],
            )
            if response.user is None:
                return False

            user = self._user_repo.get_by_id(response.user.id)
            if user is None:
                user = User(id=response.user.id, email=response.user.email)

            self._current_user = user

            # Persist refreshed tokens
            if response.session:
                self._save_session(response.session)

            return True

        except Exception:  # noqa: BLE001
            # Token may be expired or invalid — force re-login
            self._delete_session()
            return False

    # ------------------------------------------------------------------
    # Session file helpers (private)
    # ------------------------------------------------------------------

    @staticmethod
    def _save_session(session) -> None:
        """Serialise and write the Supabase session object to disk."""
        try:
            data = {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
            }
            with open(SESSION_FILE, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
        except OSError:
            pass  # Non-critical; user will need to log in again next time

    @staticmethod
    def _load_session() -> Optional[dict]:
        """Read and deserialise the session cache file."""
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def _delete_session() -> None:
        """Remove the session cache file on logout."""
        try:
            os.remove(SESSION_FILE)
        except OSError:
            pass
