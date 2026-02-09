"""Planning phase handler."""

from datetime import datetime
from typing import TYPE_CHECKING, Callable

from app.agent.formatters import format_constraints
from app.agent.models import ConversationState, Phase, TravelPlan
from app.agent.prompts import get_phase_prompt
from app.agent.tools import TOOL_DEFINITIONS, execute_tool
from app.agent.utils import detect_budget_currency, get_current_date_context

if TYPE_CHECKING:
    from app.agent.ai_client import AIClient


def generate_plan(
    client: "AIClient",
    state: ConversationState,
    search_results: list[str],
    user_interests: list[str],
    on_tool_call: Callable[[str, dict], None] | None = None,
) -> str:
    """Generate the travel itinerary.

    Args:
        client: AI client instance.
        state: Conversation state to update.
        search_results: List of previous search results.
        user_interests: List of user interests/adjustments.
        on_tool_call: Optional callback for tool calls.

    Returns:
        Day-by-day travel plan.
    """
    from app.agent.formatters import format_plan

    system_prompt = get_phase_prompt("planning")

    constraints_text = format_constraints(state)
    assumptions_text = ""
    if state.assumptions:
        assumptions_text = "\n\nConfirmed Assumptions:\n"
        for a in state.assumptions.assumptions:
            assumptions_text += f"• {a}\n"

    # Include previous search context
    search_context = ""
    if search_results:
        search_context = "\n\nPrevious research findings:\n" + "\n".join(
            search_results[-3:]
        )

    # Include user interests
    interests_text = ""
    if user_interests:
        interests_text = "\n\nUser's specific interests to incorporate:\n"
        for interest in user_interests:
            interests_text += f"• {interest}\n"

    # First gather planning-specific information including prices
    date_context = get_current_date_context()
    budget_currency = detect_budget_currency(state)

    research_prompt = f"""Generate a day-by-day itinerary for this trip:

{date_context}

{constraints_text}{assumptions_text}{interests_text}{search_context}

PREVIOUS RESEARCH is provided above. Do NOT re-search for information already available there (e.g., if flight prices, hostel prices, or attraction info is already present, skip those searches).

Only search for information NOT already covered. Typical gaps to fill:
- Local transport costs (train passes, metro, taxi) if not already researched
- Specific attraction entry fees if not already researched
- Average meal costs if not already researched
- Offbeat or hidden-gem places near the main destinations
- Any events/activities matching user interests with dates and ticket prices

IMPORTANT:
- Use the CURRENT YEAR ({datetime.now().year}) in all search queries.
- ALL prices must be in {budget_currency} (the user's currency). Convert if needed.
- If search results don't show exact prices, estimate CONSERVATIVELY (round UP).

Use web_search to find current prices for gaps only, then create the itinerary."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": research_prompt},
    ]

    # Gather current planning information
    planning_research = client.chat_with_tools(
        messages=messages,
        tools=TOOL_DEFINITIONS,
        tool_executor=execute_tool,
        temperature=0.5,
        max_tool_calls=8,
        on_tool_call=on_tool_call,
    )

    # Now generate structured plan with gathered info
    plan_prompt = f"""Create a structured day-by-day itinerary based on this information:

{constraints_text}{assumptions_text}{interests_text}

Research findings (use these for accurate cost estimates):
{planning_research}

REQUIREMENTS:
1. Commit to ONE specific route
2. Each activity MUST be a JSON object with "activity" (description), "cost_estimate" (e.g. "₹2,000", "Free"), and optional "cost_notes" keys. Do NOT use plain strings for activities.
   Example: {{"activity": "Visit Senso-ji Temple", "cost_estimate": "Free", "cost_notes": null}}
3. Include daily totals (accommodation + meals + transport + activities)
4. Include complete BUDGET BREAKDOWN at the end
5. If user mentioned specific interests (tech events, etc.), include relevant events with dates and costs
6. For EVERY day, include 2-4 tips: money-saving hacks, faster/cheaper travel alternatives, must-try food, offbeat hidden-gem spots nearby, or important warnings
7. Include 4-6 general_tips for the whole trip: visa info, SIM/connectivity, cultural etiquette, essential apps, money exchange, packing tips

CURRENCY (CRITICAL): ALL prices MUST be in {budget_currency}. Convert local prices to {budget_currency}. Do NOT mix currencies.

Provide realistic estimates based on research."""

    plan_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": plan_prompt},
    ]

    plan = client.chat_structured(plan_messages, TravelPlan, temperature=0.7)
    state.current_plan = plan
    state.phase = Phase.REFINEMENT

    response = format_plan(plan)
    response += "\n\n---\nWant me to tweak anything? I can make it safer, faster, more comfortable, or change the base location. Or if you're happy with it, we're done!"

    state.add_message("assistant", response)
    return response
