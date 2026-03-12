"""
LoginScreen — handles user sign-in UI logic.

Responsibilities:
  - Collects email / password input from the KV layout.
  - Delegates authentication to AuthService.
  - Navigates to HomeScreen on success or shows an error label.
  - Provides a link to the SignupScreen for new users.

The screen is intentionally thin: all validation and AUTH API calls
happen inside AuthService, keeping the screen focused on UI state.
"""

from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty
from kivymd.uix.screen import MDScreen

from habit_app.services.auth_service import AuthService


class LoginScreen(MDScreen):
    """
    Login screen controller.

    KV bindings:
        error_message (StringProperty): Displayed under the form on
            validation or API errors.
        is_loading (BooleanProperty): Shows a spinner and disables
            the login button while the API call is in progress.
    """

    error_message = StringProperty("")
    is_loading = BooleanProperty(False)

    def __init__(self, auth_service: AuthService, **kwargs):
        """
        Args:
            auth_service: Shared AuthService instance injected by the
                App class so all screens share one session.
        """
        super().__init__(**kwargs)
        self._auth = auth_service

    # ------------------------------------------------------------------
    # UI event handlers (called from KV)
    # ------------------------------------------------------------------

    def on_login_pressed(self) -> None:
        """
        Handle the login button press.

        Reads email/password from the KV text fields (accessed via their
        `ids`), calls AuthService, then either navigates to the home
        screen or shows an error message.
        """
        email = self.ids.email_field.text.strip()
        password = self.ids.password_field.text

        if not email or not password:
            self.error_message = "Please fill in both fields."
            return

        self.error_message = ""
        self.is_loading = True

        # Run the blocking network call off the main thread via Clock
        # to keep the UI responsive.  In production replace with a
        # proper async worker (threading.Thread or asyncio).
        Clock.schedule_once(lambda dt: self._do_login(email, password), 0.1)

    def on_signup_pressed(self) -> None:
        """Navigate to the SignupScreen."""
        self.manager.current = "signup"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _do_login(self, email: str, password: str) -> None:
        """Execute the sign-in API call and handle the result."""
        success, message, user = self._auth.sign_in(email, password)
        self.is_loading = False

        if success:
            # Pass the authenticated user to HomeScreen
            home = self.manager.get_screen("home")
            home.user = user
            self.manager.current = "home"
            # Clear form fields on successful login
            self.ids.email_field.text = ""
            self.ids.password_field.text = ""
        else:
            self.error_message = message
