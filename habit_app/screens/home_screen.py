"""
HomeScreen — main dashboard shown after login.

Responsibilities:
  - Displays the user's active habits with today's progress.
  - Shows a motivational quote of the day.
  - Provides buttons to create a new habit and navigate to profile.
  - Handles quick progress increment/decrement from habit cards.
  - Loads data asynchronously to keep the UI responsive.

Data flow:
  HomeScreen → HabitService.get_habits_for_user()
              → HabitService.get_progress_summary()
              → QuoteService.get_random_quote()
              → StreakService.get_streak()  (per habit card)
"""

from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivymd.uix.screen import MDScreen

from habit_app.models.user import User
from habit_app.services.habit_service import HabitService
from habit_app.services.streak_service import StreakService
from habit_app.services.quote_service import QuoteService


class HomeScreen(MDScreen):
    """
    Dashboard screen controller.

    Attributes:
        user (User | None): The currently authenticated user.  Set by
            LoginScreen/SignupScreen before navigating here.
        quote_text (StringProperty): Bound to the motivational quote
            label in the KV layout.
        is_loading (BooleanProperty): Shows a loading overlay while
            habits and progress are being fetched.
    """

    user: User = ObjectProperty(None, allownone=True)
    quote_text = StringProperty("")
    is_loading = BooleanProperty(False)

    def __init__(
        self,
        habit_service: HabitService,
        streak_service: StreakService,
        quote_service: QuoteService,
        **kwargs,
    ):
        """
        Args:
            habit_service: Shared HabitService instance.
            streak_service: Shared StreakService instance.
            quote_service: Shared QuoteService instance.
        """
        super().__init__(**kwargs)
        self._habit_svc = habit_service
        self._streak_svc = streak_service
        self._quote_svc = quote_service
        self._habits = []

    # ------------------------------------------------------------------
    # Kivy lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        """
        Called by Kivy every time this screen becomes active.

        Refreshes the habit list and quote to reflect any changes made
        in other screens (e.g. after creating or editing a habit).
        """
        self._load_data()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_data(self) -> None:
        """Kick off a data refresh from the backend."""
        if self.user is None:
            return
        self.is_loading = True
        Clock.schedule_once(lambda dt: self._fetch_and_render(), 0.05)

    def _fetch_and_render(self) -> None:
        """
        Fetch habits and progress from the service layer, then
        populate the UI widgets.
        """
        try:
            # 1. Load habits
            self._habits = self._habit_svc.get_habits_for_user(self.user.id)

            # 2. Load daily progress summary (batched)
            summary = self._habit_svc.get_progress_summary(self._habits)

            # 3. Load motivational quote
            quote = self._quote_svc.get_random_quote()
            self.quote_text = f'"{quote.text}"\n— {quote.author}'

            # 4. Populate the habit list widget with data
            self._populate_habit_list(summary)

        except Exception as exc:  # noqa: BLE001
            # Surface the error without crashing
            self.quote_text = f"Failed to load habits: {exc}"
        finally:
            self.is_loading = False

    def _populate_habit_list(self, summary: dict) -> None:
        """
        Clear and rebuild the habits RecycleView / MDList.

        Args:
            summary: Dict from HabitService.get_progress_summary().
        """
        habit_list = self.ids.get("habit_list")
        if habit_list is None:
            return  # KV widget not yet attached

        habit_list.clear_widgets()
        for habit in self._habits:
            stats = summary.get(habit.id, {})
            # Import here to avoid circular import at module level
            from habit_app.screens.habit_card_widget import HabitCardWidget
            card = HabitCardWidget(
                habit=habit,
                progress=stats.get("progress", 0.0),
                percentage=stats.get("percentage", 0.0),
                is_complete=stats.get("is_complete", False),
                on_increment=self.on_habit_increment,
                on_decrement=self.on_habit_decrement,
                on_tap=self.on_habit_tap,
            )
            habit_list.add_widget(card)

    # ------------------------------------------------------------------
    # UI event handlers
    # ------------------------------------------------------------------

    def on_habit_increment(self, habit_id: str) -> None:
        """
        Log +1 unit of progress for the tapped habit card's + button.

        Args:
            habit_id: UUID of the habit to increment.
        """
        habit = next((h for h in self._habits if h.id == habit_id), None)
        if habit is None:
            return
        success, _, _ = self._habit_svc.log_progress(habit_id, 1.0)
        if success:
            self._load_data()  # Refresh to show new progress

    def on_habit_decrement(self, habit_id: str) -> None:
        """
        Log -1 unit of progress for habits that support it.

        Args:
            habit_id: UUID of the habit to decrement.
        """
        success, _, _ = self._habit_svc.decrement_progress(habit_id, 1.0)
        if success:
            self._load_data()

    def on_habit_tap(self, habit_id: str) -> None:
        """
        Navigate to HabitDetailScreen for the tapped habit.

        Args:
            habit_id: UUID of the tapped habit.
        """
        detail = self.manager.get_screen("habit_detail")
        detail.habit_id = habit_id
        detail.user = self.user
        self.manager.current = "habit_detail"

    def on_create_habit_pressed(self) -> None:
        """Navigate to CreateHabitScreen."""
        create = self.manager.get_screen("create_habit")
        create.user = self.user
        self.manager.current = "create_habit"

    def on_profile_pressed(self) -> None:
        """Navigate to ProfileScreen."""
        profile = self.manager.get_screen("profile")
        profile.user = self.user
        self.manager.current = "profile"
