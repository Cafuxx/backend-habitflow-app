"""
main.py — HabitFlow application entry point.

Bootstrap sequence:
  1. Load all KV layout files from habit_app/kv/.
  2. Instantiate shared service objects (AuthService, HabitService, …).
  3. Build the ScreenManager with all screens.
  4. Attempt to restore a saved session; navigate to HomeScreen if
     successful, otherwise show LoginScreen.

Architecture note:
  Services are created once here and injected into every screen that
  needs them.  This is a manual dependency-injection pattern — simple
  enough for a mobile app of this size, and easy to replace with a
  proper DI container later.
"""

import os

from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

# ── Service layer ──────────────────────────────────────────────────────────
from habit_app.services.auth_service import AuthService
from habit_app.services.habit_service import HabitService
from habit_app.services.streak_service import StreakService
from habit_app.services.quote_service import QuoteService

# ── Screens ────────────────────────────────────────────────────────────────
from habit_app.screens.login_screen import LoginScreen
from habit_app.screens.signup_screen import SignupScreen
from habit_app.screens.home_screen import HomeScreen
from habit_app.screens.create_habit_screen import CreateHabitScreen
from habit_app.screens.habit_detail_screen import HabitDetailScreen
from habit_app.screens.profile_screen import ProfileScreen

# ── KV files directory ─────────────────────────────────────────────────────
KV_DIR = os.path.join(os.path.dirname(__file__), "habit_app", "kv")


def _load_kv_files() -> None:
    """
    Load all .kv layout files from the kv/ directory.

    KivyMD does NOT auto-discover kv files for MDScreen subclasses the
    same way plain Kivy does for App subclasses, so we load them
    explicitly here to keep control over load order.
    """
    kv_files = [
        "login_screen.kv",
        "home_screen.kv",
        "habit_card.kv",
    ]
    for filename in kv_files:
        path = os.path.join(KV_DIR, filename)
        if os.path.isfile(path):
            Builder.load_file(path)


class HabitFlowApp(MDApp):
    """
    Root application class.

    KivyMD theme is configured here.  All service instances are
    created in `build()` and injected into screens so that the
    entire app shares a single session and service state.
    """

    def build(self) -> MDScreenManager:
        """
        Initialise theme, load KV files, create services, and wire screens.

        Returns:
            The root ScreenManager widget.
        """
        # ── Theme ──────────────────────────────────────────────────────
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Pink"
        self.theme_cls.theme_style = "Light"  # "Dark" also supported

        # Comfortable default size in development / desktop testing
        Window.size = (390, 844)  # iPhone 14 logical resolution

        # ── Load KV layout files ───────────────────────────────────────
        _load_kv_files()

        # ── Instantiate shared services ────────────────────────────────
        auth_service = AuthService()
        habit_service = HabitService()
        streak_service = StreakService()
        quote_service = QuoteService()

        # ── Build ScreenManager ────────────────────────────────────────
        sm = MDScreenManager()

        sm.add_widget(LoginScreen(auth_service=auth_service, name="login"))
        sm.add_widget(SignupScreen(auth_service=auth_service, name="signup"))
        sm.add_widget(
            HomeScreen(
                habit_service=habit_service,
                streak_service=streak_service,
                quote_service=quote_service,
                name="home",
            )
        )
        sm.add_widget(
            CreateHabitScreen(habit_service=habit_service, name="create_habit")
        )
        sm.add_widget(
            HabitDetailScreen(
                habit_service=habit_service,
                streak_service=streak_service,
                name="habit_detail",
            )
        )
        sm.add_widget(ProfileScreen(auth_service=auth_service, name="profile"))

        # ── Session restore ────────────────────────────────────────────
        #
        # Try to restore a saved session from disk.  If it succeeds the
        # user goes straight to the home screen; otherwise they land on
        # the login screen.
        #
        try:
            if auth_service.restore_session() and auth_service.current_user:
                home = sm.get_screen("home")
                home.user = auth_service.current_user
                sm.current = "home"
            else:
                sm.current = "login"
        except Exception:  # noqa: BLE001
            sm.current = "login"

        return sm


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    HabitFlowApp().run()
