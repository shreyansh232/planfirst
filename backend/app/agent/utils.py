"""Utility functions for the travel agent."""

from datetime import datetime

from app.agent.models import ConversationState


def get_current_date_context() -> str:
    """Get current date context for prompts.

    Returns:
        Formatted date string with year.
    """
    now = datetime.now()
    return f"Today's date: {now.strftime('%B %d, %Y')} (Year: {now.year})"


def detect_budget_currency(state: ConversationState) -> str:
    """Detect the user's preferred currency from their budget string.

    Args:
        state: Current conversation state.

    Returns:
        Currency code string (e.g., 'INR', 'USD', 'EUR').
    """
    if not state.constraints or not state.constraints.budget:
        return "USD"

    budget_str = state.constraints.budget.upper()
    currency_map = {
        ("INR", "₹", "LAKH", "RUPEE"): "INR",
        ("USD", "$", "DOLLAR"): "USD",
        ("EUR", "€", "EURO"): "EUR",
        ("JPY", "¥", "YEN"): "JPY",
        ("GBP", "£", "POUND"): "GBP",
        ("THB", "BAHT"): "THB",
        ("AUD", "A$"): "AUD",
        ("CAD", "C$"): "CAD",
        ("SGD", "S$"): "SGD",
    }
    for keywords, code in currency_map.items():
        if any(kw in budget_str for kw in keywords):
            return code
    return "USD"
