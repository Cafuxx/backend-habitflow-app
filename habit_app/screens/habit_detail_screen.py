"""
HabitDetailScreen — displays full statistics for a single habit.

Responsibilities:
  - Shows the habit name, icon, goal, and description.
  - Displays today's progress and percentage bar.
  - Shows current streak and longest streak from StreakService.
  - Provides Edit and Delete action buttons.
  - Loads all data via HabitService and StreakService.
"""

from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivymd.uix.screen import MDScreen

from habit_app.models.user import User
from habit_app.services.habit_service import HabitService
from habit_app.services.streak_service import StreakService


class HabitDetailScreen(MDScreen):
    """
    Detail / statistics screen for a single habit.

    KV bindings:
        habit_name (str): Habit display name.
        habit_icon (str): Icon identifier.
        goal_label (str): Human-readable goal description.
        progress (float): Today's progress value.
        percentage (float): Completion percentage.
        current_streak (int): Current consecutive streak.
        longest_streak (int): Best streak ever.
        is_complete_today (bool): Goal met today flag.
        is_loading (bool): Loading overlay flag.
    """

    habit_id: str = StringProperty("")
    user: User = ObjectProperty(None, allownone=True)

    habit_name = StringProperty("")
    habit_icon = StringProperty("star-outline")
    goal_label = StringProperty("")
    progress = NumericProperty(0.0)
    percentage = NumericProperty(0.0)
    current_streak = NumericProperty(0)
    longest_streak = NumericProperty(0)
    is_complete_today = BooleanProperty(False)
    is_loading = BooleanProperty(False)

    def __init__(
        self,
        habit_service: HabitService,
        streak_service: StreakService,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._habit_svc = habit_service
        self._streak_svc = streak_service
        self._habit = None  # Loaded on enter

    # ------------------------------------------------------------------
    # Kivy lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        """Load habit data whenever the screen becomes active."""
        self._load_data()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_data(self) -> None:
        if not self.habit_id or self.user is None:
            return
        self.is_loading = True
        Clock.schedule_once(lambda dt: self._fetch(), 0.05)

    def _fetch(self) -> None:
        try:
            habit = self._habit_svc.get_habit_by_id(
                self.habit_id, self.user.id
            )
            if habit is None:
                self.manager.current = "home"
                return

            self._habit = habit

            # Progress
            progress = self._habit_svc.get_today_progress(habit.id)
            percentage = self._habit_svc.get_progress_percentage(habit)

            # Streak
            streak_result = self._streak_svc.get_streak(habit)

            # Populate bindings
            self.habit_name = habit.name
            self.habit_icon = habit.icon
            self.goal_label = (
                f"Goal: {habit.goal_value} {habit.goal_type} per day"
            )
            self.progress = progress
            self.percentage = percentage
            self.current_streak = streak_result.current_streak
            self.longest_streak = streak_result.longest_streak
            self.is_complete_today = streak_result.is_complete_today

        except Exception as exc:  # noqa: BLE001
            self.habit_name = f"Error loading habit: {exc}"
        finally:
            self.is_loading = False

    # ------------------------------------------------------------------
    # UI event handlers
    # ------------------------------------------------------------------

    def on_edit_pressed(self) -> None:
        """Navigate to CreateHabitScreen pre-filled with current data."""
        if self._habit is None:
            return
        edit_screen = self.manager.get_screen("create_habit")
        edit_screen.user = self.user
        # Pre-fill form fields — the KV file binds these via ids
        edit_screen.ids.name_field.text = self._habit.name
        edit_screen.ids.goal_value_field.text = str(self._habit.goal_value)
        edit_screen.selected_icon = self._habit.icon
        edit_screen.selected_goal_type = self._habit.goal_type
        # Store the habit being edited so the save handler knows to call update
        edit_screen._editing_habit = self._habit
        self.manager.current = "create_habit"

    def on_delete_pressed(self) -> None:
        """
        Confirm and soft-delete the current habit.

        In production replace with an MDDialog confirmation popup
        before calling the service.
        """
        if self._habit is None or self._habit.id is None:
            return
        success, _ = self._habit_svc.delete_habit(
            self._habit.id, self.user.id
        )
        if success:
            self.manager.current = "home"

    def on_back_pressed(self) -> None:
        """Navigate back to HomeScreen."""
        self.manager.current = "home"
