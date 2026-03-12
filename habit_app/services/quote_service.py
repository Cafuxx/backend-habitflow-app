"""
QuoteService — motivational quote storage and retrieval.

Current implementation:
  - Stores a curated set of motivational quotes locally in the app
    (no network request required; works offline).
  - Provides a `get_random_quote()` method for the home screen.

Architecture is designed for easy extension:
  - The `_fetch_from_api()` stub can be wired to an external API
    or a Supabase `quotes` table with zero interface changes.
  - An AI-generated quote feature can override `get_random_quote()`
    by calling an LLM endpoint and falling back to local quotes on
    network failure.

Future feature hooks (structure prepared, not implemented):
  - `get_ai_quote(topic: str)` — AI-generated personalised quote.
  - `get_quote_for_habit(habit_name: str)` — category-specific quote.
  - `get_quote_of_the_day()` — deterministic daily rotation from DB.
"""

import random
from dataclasses import dataclass
from typing import List, Optional


# ---------------------------------------------------------------------------
# Value object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Quote:
    """
    Represents a motivational quote.

    Attributes:
        text (str): The quote body.
        author (str): Author name or "Unknown".
        category (str): Topic tag for future AI/category filtering.
    """
    text: str
    author: str = "Unknown"
    category: str = "general"


# ---------------------------------------------------------------------------
# Curated quote bank
# ---------------------------------------------------------------------------

_QUOTE_BANK: List[Quote] = [
    Quote(
        "We are what we repeatedly do. Excellence, then, is not an act, "
        "but a habit.",
        "Aristotle",
        "discipline",
    ),
    Quote(
        "The secret of getting ahead is getting started.",
        "Mark Twain",
        "motivation",
    ),
    Quote(
        "You do not rise to the level of your goals. "
        "You fall to the level of your systems.",
        "James Clear",
        "discipline",
    ),
    Quote(
        "Small disciplines repeated with consistency every day lead to "
        "great achievements gained slowly over time.",
        "John C. Maxwell",
        "consistency",
    ),
    Quote(
        "It's not about having time. It's about making time.",
        "Unknown",
        "motivation",
    ),
    Quote(
        "Chains of habit are too light to be felt until they are too "
        "heavy to be broken.",
        "Warren Buffett",
        "discipline",
    ),
    Quote(
        "A year from now you may wish you had started today.",
        "Karen Lamb",
        "motivation",
    ),
    Quote(
        "Success is the sum of small efforts repeated day in and day out.",
        "Robert Collier",
        "consistency",
    ),
    Quote(
        "The only way to do great work is to love what you do.",
        "Steve Jobs",
        "motivation",
    ),
    Quote(
        "Don't watch the clock; do what it does. Keep going.",
        "Sam Levenson",
        "discipline",
    ),
    Quote(
        "An ounce of practice is worth more than tons of preaching.",
        "Mahatma Gandhi",
        "discipline",
    ),
    Quote(
        "Motivation is what gets you started. Habit is what keeps you "
        "going.",
        "Jim Ryun",
        "habits",
    ),
    Quote(
        "The difference between who you are and who you want to be is "
        "what you do.",
        "Unknown",
        "growth",
    ),
    Quote(
        "Every action you take is a vote for the type of person you wish "
        "to become.",
        "James Clear",
        "habits",
    ),
    Quote(
        "Consistency is more important than perfection.",
        "Unknown",
        "consistency",
    ),
    Quote(
        "The groundwork of all happiness is health.",
        "Leigh Hunt",
        "health",
    ),
    Quote(
        "Take care of your body. It's the only place you have to live.",
        "Jim Rohn",
        "health",
    ),
    Quote(
        "Reading is to the mind what exercise is to the body.",
        "Joseph Addison",
        "learning",
    ),
    Quote(
        "Your body can stand almost anything. It's your mind that you "
        "have to convince.",
        "Unknown",
        "fitness",
    ),
    Quote(
        "The mind is everything. What you think, you become.",
        "Buddha",
        "mindset",
    ),
]


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class QuoteService:
    """
    Provides motivational quotes to the application.

    The service is designed to be dependency-injectable and extend to
    remote sources (Supabase table or AI API) without changing the
    calling code.
    """

    def __init__(self, quotes: Optional[List[Quote]] = None) -> None:
        """
        Args:
            quotes: Optional custom quote list for testing or overriding
                the built-in bank.
        """
        self._quotes: List[Quote] = quotes if quotes is not None else _QUOTE_BANK

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_random_quote(self) -> Quote:
        """
        Return a randomly selected quote from the available bank.

        Returns:
            A Quote instance.
        """
        return random.choice(self._quotes)

    def get_quotes_by_category(self, category: str) -> List[Quote]:
        """
        Return all quotes matching a specific category tag.

        Args:
            category: Category string (e.g. "discipline", "health").

        Returns:
            Filtered list of Quote instances.  Empty if no matches.
        """
        return [q for q in self._quotes if q.category == category]

    def get_all_categories(self) -> List[str]:
        """Return sorted unique list of available categories."""
        return sorted({q.category for q in self._quotes})

    # ------------------------------------------------------------------
    # Future feature stubs (not implemented)
    # ------------------------------------------------------------------

    def get_ai_quote(self, topic: str) -> Quote:
        """
        [FUTURE] Generate a personalised quote using an AI API.

        Args:
            topic: Topic or habit name to generate a quote about.

        Returns:
            An AI-generated Quote, falling back to a local random quote
            on network failure.

        Note:
            This method is a placeholder.  Wire an LLM API call here
            (e.g. OpenAI, Gemini) and implement the network request
            through a dedicated AIService.
        """
        # Fallback to local quote until AI feature is built
        return self.get_random_quote()

    def get_quote_of_the_day(self, seed: Optional[int] = None) -> Quote:
        """
        [FUTURE] Return a deterministic daily quote.

        Uses the current date as the random seed so the same quote is
        shown all day, cycling through the bank.

        Args:
            seed: Optional integer seed override (for testing).

        Returns:
            Today's Quote.
        """
        from habit_app.utils.date_utils import today_local
        today = today_local()
        effective_seed = seed if seed is not None else int(today.strftime("%Y%m%d"))
        rng = random.Random(effective_seed)
        return rng.choice(self._quotes)
