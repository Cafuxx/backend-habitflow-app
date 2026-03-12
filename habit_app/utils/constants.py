"""
Application-wide constants.

======================================================
  IMPORTANT: Replace the placeholder values below
  with your actual Supabase project credentials.
  Never commit real credentials to version control.
  Use environment variables in CI/CD pipelines.
======================================================

To get your credentials:
  1. Go to https://supabase.com/dashboard
  2. Select your project → Settings → API
  3. Copy the Project URL and anon/public key.
"""

# ---------------------------------------------------------------------------
# Supabase configuration
# ---------------------------------------------------------------------------

# Your Supabase project URL (e.g. https://xyzcompany.supabase.co)
SUPABASE_URL: str = "https://dgjuardjhohrpyccbpyb.supabase.co"

# Your Supabase anon/public API key (safe to use on client side with RLS)
SUPABASE_ANON_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRnanVhcmRqaG9ocnB5Y2NicHliIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMyNjkzMjIsImV4cCI6MjA4ODg0NTMyMn0.v4NbSdTtFla-FhoQau_zPoeyIFAP-__d4-4h7kNk-TQ"

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------

APP_NAME: str = "HabitFlow"
APP_VERSION: str = "1.0.0"

# ---------------------------------------------------------------------------
# UI / UX constants
# ---------------------------------------------------------------------------

# Minimum and maximum character limits for habit names
HABIT_NAME_MIN_LENGTH: int = 2
HABIT_NAME_MAX_LENGTH: int = 60

# Password requirements
PASSWORD_MIN_LENGTH: int = 6
PASSWORD_MAX_LENGTH: int = 128

# Maximum daily goal value (prevents accidental absurd inputs)
GOAL_VALUE_MAX: float = 100_000.0

# ---------------------------------------------------------------------------
# Date / time
# ---------------------------------------------------------------------------

# ISO weekday index for "start of week" in streak display (0=Monday, 6=Sunday)
WEEK_START_DAY: int = 0  # Monday

# ---------------------------------------------------------------------------
# Icon defaults
# ---------------------------------------------------------------------------

DEFAULT_HABIT_ICON: str = "star-outline"

# Predefined icon options shown in the habit creation picker
AVAILABLE_ICONS: list = [
    "water",
    "meditation",
    "book-open-variant",
    "dumbbell",
    "run",
    "food-apple",
    "sleep",
    "pencil",
    "music",
    "heart-pulse",
    "star-outline",
    "brain",
    "bicycle",
    "yoga",
    "pill",
]

# ---------------------------------------------------------------------------
# Colour palette (hex strings — used in KV files and Python drawing)
# ---------------------------------------------------------------------------

COLOR_PRIMARY: str = "#6C63FF"       # Brand purple
COLOR_PRIMARY_DARK: str = "#4B44C9"
COLOR_SECONDARY: str = "#FF6584"     # Accent pink
COLOR_BACKGROUND: str = "#F8F8FF"    # Near-white
COLOR_SURFACE: str = "#FFFFFF"
COLOR_TEXT_PRIMARY: str = "#1A1A2E"
COLOR_TEXT_SECONDARY: str = "#6B6B8A"
COLOR_SUCCESS: str = "#4CAF50"
COLOR_WARNING: str = "#FF9800"
COLOR_ERROR: str = "#F44336"

# ---------------------------------------------------------------------------
# Notification channels (structure for future push notification feature)
# ---------------------------------------------------------------------------

# Android notification channel IDs
NOTIFICATION_CHANNEL_REMINDERS: str = "habit_reminders"
NOTIFICATION_CHANNEL_STREAKS: str = "habit_streaks"
NOTIFICATION_CHANNEL_MOTIVATION: str = "habit_motivation"
