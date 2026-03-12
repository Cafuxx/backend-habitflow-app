"""
ProfileScreen — displays user profile and account settings.

Responsibilities:
  - Shows the user's email and display name.
  - Allows the user to update their display name.
  - Provides a sign-out button.

This is intentionally minimal; future iterations can add avatar upload,
notification preferences, and social features here.
"""

from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from kivymd.uix.screen import MDScreen

from habit_app.models.user import User
from habit_app.repositories.user_repository import UserRepository
from habit_app.services.auth_service import AuthService


class ProfileScreen(MDScreen):
    """
    User profile screen controller.

    KV bindings:
        display_email (str): Read-only email shown in the header.
        display_name (str): Editable name field.
        status_message (str): Inline save/error feedback.
        is_loading (bool): Spinner shown during API calls.
    """

    user: User = ObjectProperty(None, allownone=True)
    display_email = StringProperty("")
    display_name = StringProperty("")
    status_message = StringProperty("")
    is_loading = BooleanProperty(False)

    def __init__(self, auth_service: AuthService, **kwargs):
        """
        Args:
            auth_service: Shared AuthService for sign-out.
        """
        super().__init__(**kwargs)
        self._auth = auth_service
        self._user_repo = UserRepository()

    # ------------------------------------------------------------------
    # Kivy lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        """Populate fields with current user data on screen enter."""
        if self.user:
            self.display_email = self.user.email
            self.display_name = self.user.display_name or ""
            self.status_message = ""

    # ------------------------------------------------------------------
    # UI event handlers
    # ------------------------------------------------------------------

    def on_save_pressed(self) -> None:
        """Save the updated display name to Supabase."""
        new_name = self.ids.name_field.text.strip()
        if not new_name:
            self.status_message = "Display name cannot be empty."
            return

        self.is_loading = True
        self.status_message = ""
        Clock.schedule_once(
            lambda dt: self._do_save_name(new_name), 0.1
        )

    def on_signout_pressed(self) -> None:
        """Sign out and return to the login screen."""
        self._auth.sign_out()
        self.manager.current = "login"

    def on_back_pressed(self) -> None:
        """Navigate back to HomeScreen."""
        self.manager.current = "home"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _do_save_name(self, new_name: str) -> None:
        try:
            self._user_repo.update_display_name(self.user.id, new_name)
            # Keep in-memory user object in sync
            self.user.display_name = new_name
            self.display_name = new_name
            self.status_message = "Profile updated."
        except Exception as exc:  # noqa: BLE001
            self.status_message = f"Failed to save: {exc}"
        finally:
            self.is_loading = False
