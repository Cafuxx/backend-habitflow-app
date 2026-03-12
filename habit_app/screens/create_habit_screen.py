"""
CreateHabitScreen — form for creating a new habit.

Responsibilities:
  - Provides input fields for name, icon, goal_type, goal_value,
    and optional reminder time.
  - Validates inputs via HabitService (which delegates to validators).
  - Calls HabitService.create_habit() on submit.
  - Navigates back to HomeScreen on success.
"""

from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivymd.uix.screen import MDScreen

from habit_app.models.habit import GoalType
from habit_app.models.user import User
from habit_app.services.habit_service import HabitService
from habit_app.utils.constants import DEFAULT_HABIT_ICON, AVAILABLE_ICONS


class CreateHabitScreen(MDScreen):
    """
    Habit creation form screen.

    KV bindings:
        error_message (StringProperty): Inline error below the form.
        is_loading (BooleanProperty): Disables the Save button
            during the API call.
        selected_icon (StringProperty): Currently chosen icon identifier.
        selected_goal_type (StringProperty): Currently chosen GoalType.
    """

    user: User = ObjectProperty(None, allownone=True)
    error_message = StringProperty("")
    is_loading = BooleanProperty(False)
    selected_icon = StringProperty(DEFAULT_HABIT_ICON)
    selected_goal_type = StringProperty(GoalType.NUMBER)

    # Expose constants for KV access
    GOAL_TYPES = GoalType.ALL
    AVAILABLE_ICONS = AVAILABLE_ICONS

    def __init__(self, habit_service: HabitService, **kwargs):
        """
        Args:
            habit_service: Shared HabitService instance.
        """
        super().__init__(**kwargs)
        self._habit_svc = habit_service

    # ------------------------------------------------------------------
    # UI event handlers
    # ------------------------------------------------------------------

    def on_icon_selected(self, icon: str) -> None:
        """
        Update the selected icon when the user taps an icon in the picker.

        Args:
            icon: Material Design icon name string.
        """
        self.selected_icon = icon

    def on_goal_type_selected(self, goal_type: str) -> None:
        """
        Update the selected goal type when the user taps a chip.

        Args:
            goal_type: One of GoalType constants.
        """
        self.selected_goal_type = goal_type

    def on_save_pressed(self) -> None:
        """
        Validate and submit the new habit creation form.
        """
        name = self.ids.name_field.text.strip()
        goal_value_raw = self.ids.goal_value_field.text.strip()
        reminder_raw = self.ids.get("reminder_field", None)

        if not name:
            self.error_message = "Please enter a habit name."
            return

        try:
            goal_value = float(goal_value_raw) if goal_value_raw else 1.0
        except ValueError:
            self.error_message = "Goal value must be a number."
            return

        # Parse optional reminder time
        reminder_time = None
        if reminder_raw and reminder_raw.text:
            from datetime import time
            parts = reminder_raw.text.strip().split(":")
            try:
                reminder_time = time(int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                self.error_message = "Invalid reminder time format (HH:MM)."
                return

        self.error_message = ""
        self.is_loading = True
        Clock.schedule_once(
            lambda dt: self._do_create(name, goal_value, reminder_time), 0.1
        )

    def on_cancel_pressed(self) -> None:
        """Discard the form and go back to HomeScreen."""
        self._reset_form()
        self.manager.current = "home"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _do_create(self, name: str, goal_value: float, reminder_time) -> None:
        """Execute the API call and handle the response."""
        success, message, habit = self._habit_svc.create_habit(
            user_id=self.user.id,
            name=name,
            icon=self.selected_icon,
            goal_type=self.selected_goal_type,
            goal_value=goal_value,
            reminder_time=reminder_time,
        )
        self.is_loading = False

        if success:
            self._reset_form()
            self.manager.current = "home"
        else:
            self.error_message = message

    def _reset_form(self) -> None:
        """Clear all input fields back to defaults."""
        self.ids.name_field.text = ""
        self.ids.goal_value_field.text = ""
        self.selected_icon = DEFAULT_HABIT_ICON
        self.selected_goal_type = GoalType.NUMBER
        self.error_message = ""
