"""
SignupScreen — handles new user registration UI logic.

Responsibilities:
  - Collects email / password / confirm-password from the KV layout.
  - Performs client-side password match check before calling the API.
  - Delegates registration to AuthService.
  - Navigates to HomeScreen on success.
"""

from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty
from kivymd.uix.screen import MDScreen

from habit_app.services.auth_service import AuthService


class SignupScreen(MDScreen):
    """
    Signup / registration screen controller.

    KV bindings:
        error_message (StringProperty): Inline error shown on the form.
        is_loading (BooleanProperty): Disables controls during the
            API call.
    """

    error_message = StringProperty("")
    is_loading = BooleanProperty(False)

    def __init__(self, auth_service: AuthService, **kwargs):
        """
        Args:
            auth_service: Shared AuthService instance.
        """
        super().__init__(**kwargs)
        self._auth = auth_service

    # ------------------------------------------------------------------
    # UI event handlers (called from KV)
    # ------------------------------------------------------------------

    def on_signup_pressed(self) -> None:
        """
        Handle the sign-up button press.

        Validates that passwords match before delegating to AuthService.
        """
        email = self.ids.email_field.text.strip()
        password = self.ids.password_field.text
        confirm = self.ids.confirm_password_field.text

        if not email or not password or not confirm:
            self.error_message = "Please fill in all fields."
            return

        if password != confirm:
            self.error_message = "Passwords do not match."
            return

        self.error_message = ""
        self.is_loading = True
        Clock.schedule_once(
            lambda dt: self._do_signup(email, password), 0.1
        )

    def on_login_pressed(self) -> None:
        """Navigate back to LoginScreen."""
        self.manager.current = "login"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _do_signup(self, email: str, password: str) -> None:
        """Execute the sign-up API call and handle the result."""
        success, message, user = self._auth.sign_up(email, password)
        self.is_loading = False

        if success:
            home = self.manager.get_screen("home")
            home.user = user
            self.manager.current = "home"
        else:
            self.error_message = message
