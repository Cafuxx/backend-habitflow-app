"""
HabitCardWidget — reusable card widget for habit list items.

This widget is used by HomeScreen to display a single habit with its
daily progress bar, streak badge, increment/decrement buttons,
and completion indicator.

It is a self-contained MDCard subclass that receives its data through
constructor arguments and fires callbacks back to the parent screen.
"""

from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivymd.uix.card import MDCard


class HabitCardWidget(MDCard):
    """
    Displays one habit in the home screen list.

    Attributes:
        habit_name (str): Displayed habit title.
        habit_icon (str): Material Design icon name.
        progress (float): Today's logged value.
        goal_value (float): Daily target.
        percentage (float): Completion percentage (0–100).
        is_complete (bool): True when goal has been reached today.
        streak (int): Current streak count (set by parent after
            StreakService call, default 0).
    """

    habit_name = StringProperty("")
    habit_icon = StringProperty("star-outline")
    progress = NumericProperty(0.0)
    goal_value = NumericProperty(1.0)
    percentage = NumericProperty(0.0)
    is_complete = BooleanProperty(False)
    streak = NumericProperty(0)

    def __init__(
        self,
        habit,
        progress: float,
        percentage: float,
        is_complete: bool,
        on_increment,
        on_decrement,
        on_tap,
        **kwargs,
    ):
        """
        Args:
            habit: Habit model instance.
            progress: Today's raw progress value.
            percentage: Completion percentage (0–100).
            is_complete: Whether the daily goal has been met.
            on_increment: Callback(habit_id) for + button.
            on_decrement: Callback(habit_id) for - button.
            on_tap: Callback(habit_id) when card body is tapped.
        """
        super().__init__(**kwargs)
        self._habit = habit
        self._on_increment = on_increment
        self._on_decrement = on_decrement
        self._on_tap = on_tap

        # Set KV-bindable properties from model data
        self.habit_name = habit.name
        self.habit_icon = habit.icon
        self.goal_value = habit.goal_value
        self.progress = progress
        self.percentage = percentage
        self.is_complete = is_complete

    # ------------------------------------------------------------------
    # Touch/button handlers (wired up in habit_card.kv)
    # ------------------------------------------------------------------

    def handle_increment(self) -> None:
        """Called when the + button is pressed."""
        self._on_increment(self._habit.id)

    def handle_decrement(self) -> None:
        """Called when the - button is pressed."""
        self._on_decrement(self._habit.id)

    def handle_tap(self) -> None:
        """Called when the card body is tapped (navigate to detail)."""
        self._on_tap(self._habit.id)
