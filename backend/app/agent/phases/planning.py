"""Planning phase handler."""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Iterator

from app.agent.formatters import format_constraints, format_plan
from app.agent.models import ConversationState, Phase, TravelPlan
from app.agent.prompts import get_phase_prompt
from app.agent.tools import TOOL_DEFINITIONS, execute_tool
from app.agent.trust import enrich_plan_with_trust_metadata
from app.agent.utils import detect_budget_currency, get_current_date_context

if TYPE_CHECKING:
    from app.agent.ai_client import AIClient

logger = logging.getLogger(__name__)

PLAN_PARSE_SYSTEM_PROMPT = """You convert itinerary text into structured TravelPlan JSON.

Extraction rules:
- Return only JSON matching the TravelPlan schema.
- Preserve concrete itinerary details (days, activities, costs, route).
- If a value is missing, use sensible empty values (empty list / null) rather than inventing.
- Keep prices and route wording faithful to the itinerary text.
"""


def _trim_for_parse(text: str, max_chars: int) -> str:
    """Trim large text payloads to keep structured parsing stable."""
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-(max_chars // 2) :]
    return f"{head}\n\n...[truncated for parsing]...\n\n{tail}"


def _parse_plan_from_text(
    client: "AIClient",
    full_response: str,
    research_context: str,
) -> TravelPlan:
    """Parse streamed itinerary text into structured TravelPlan."""
    itinerary_excerpt = _trim_for_parse(full_response.strip(), 24_000)
    research_excerpt = _trim_for_parse(research_context.strip(), 8_000)

    attempts = [
        {"include_research": True, "include_schema": True, "include_example": True},
        {"include_research": False, "include_schema": True, "include_example": True},
        {"include_research": False, "include_schema": False, "include_example": True},
    ]
    last_error: Exception | None = None

    for idx, options in enumerate(attempts, start=1):
        context_block = (
            f"\n\nResearch context (optional support):\n{research_excerpt}"
            if options["include_research"] and research_excerpt
            else ""
        )
        structured_prompt = f"""Extract a TravelPlan JSON object from this itinerary text.

Itinerary text:
{itinerary_excerpt}
{context_block}

Critical extraction rules:
- Populate `flights` with 2-4 bookable options when route data is available.
- Populate `lodgings` with 3-5 options and direct booking links.
- Preserve day-wise activity and budget details.
- Do not add sections that are not present in the itinerary."""
        try:
            return client.chat_structured(
                [
                    {"role": "system", "content": PLAN_PARSE_SYSTEM_PROMPT},
                    {"role": "user", "content": structured_prompt},
                ],
                TravelPlan,
                temperature=0.0,
                max_retries=1,
                include_schema=options["include_schema"],
                include_example=options["include_example"],
            )
        except Exception as exc:  # pragma: no cover - network/provider variability
            last_error = exc
            logger.warning(
                "Plan structuring attempt %s failed (research=%s, schema=%s): %s",
                idx,
                options["include_research"],
                options["include_schema"],
                exc,
            )

    if last_error:
        raise last_error
    raise ValueError("Failed to structure streamed itinerary into TravelPlan.")


def _gather_planning_research(
    client: "AIClient",
    state: ConversationState,
    search_results: list[str],
    user_interests: list[str],
    on_tool_call: Callable[[str, dict], None] | None = None,
    language_code: str | None = None,
) -> str:
    """Helper to gather planning-specific info via web search."""
    vibe = state.vibe or (state.constraints.vibe if state.constraints else None)
    system_prompt = get_phase_prompt("planning", language_code, vibe=vibe)
    constraints_text = format_constraints(state)
    assumptions_text = ""
    if state.assumptions:
        assumptions_text = "\n\nConfirmed Assumptions:\n"
        for a in state.assumptions.assumptions:
            assumptions_text += f"• {a}\n"

    search_context = ""
    if search_results:
        search_context = "\n\nPrevious research findings:\n" + "\n".join(
            search_results[-3:]
        )

    interests_text = ""
    if user_interests:
        interests_text = "\n\nUser's specific interests to incorporate:\n"
        for interest in user_interests:
            interests_text += f"• {interest}\n"

    date_context = get_current_date_context()
    budget_currency = detect_budget_currency(state)

    research_prompt = f"""Generate a day-by-day itinerary for this trip:

{date_context}

{constraints_text}{assumptions_text}{interests_text}{search_context}

PREVIOUS RESEARCH is provided above. Do NOT re-search for information already available there.

Only search for information NOT already covered. Typical gaps:
- Specific attraction entry fees
- Average meal costs
- Flight/Transport costs from origin to destination (if origin is known)
- Offbeat spots matching interests

IMPORTANT:
- Use the CURRENT YEAR ({datetime.now().year}) in all search queries.
- ALL prices must be in {budget_currency}.

Use web_search to find current prices for gaps only, then return the findings."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": research_prompt},
    ]

    return client.chat_with_tools(
        messages=messages,
        tools=TOOL_DEFINITIONS,
        tool_executor=execute_tool,
        temperature=0.7,
        max_tool_calls=1,
        on_tool_call=on_tool_call,
    )


def _has_train_research(search_results: list[str]) -> bool:
    return any("Train Cost Estimates (" in block for block in search_results[-8:])


def _append_train_research(
    state: ConversationState,
    search_results: list[str],
    train_costs: dict | None = None,
) -> None:
    """Attach train research once; prefer cached background results."""
    if train_costs and train_costs.get("summary"):
        if train_costs["summary"] not in search_results:
            search_results.append(train_costs["summary"])
        return

    if _has_train_research(search_results):
        return

    if not (state.origin and state.destination):
        return

    from app.agent.train_search import search_train_costs, should_search_trains

    if should_search_trains(state.origin, state.destination):
        date_ctx = state.constraints.month_or_season if state.constraints else None
        budget = state.constraints.budget if state.constraints else None
        tc = search_train_costs(state.origin, state.destination, date_ctx, budget)
        if tc and tc.get("summary"):
            search_results.append(tc["summary"])


def generate_plan(
    client: "AIClient",
    state: ConversationState,
    search_results: list[str],
    user_interests: list[str],
    on_tool_call: Callable[[str, dict], None] | None = None,
    language_code: str | None = None,
    train_costs: dict | None = None,
) -> str:
    """Generate the travel itinerary (non-streaming)."""
    planning_research = _gather_planning_research(
        client,
        state,
        search_results,
        user_interests,
        on_tool_call=on_tool_call,
        language_code=language_code,
    )
    search_results.append(planning_research)

    vibe = state.vibe or (state.constraints.vibe if state.constraints else None)
    system_prompt = get_phase_prompt("planning", language_code, vibe=vibe)
    constraints_text = format_constraints(state)
    assumptions_text = ""
    if state.assumptions:
        assumptions_text = "\n\nConfirmed Assumptions:\n"
        for a in state.assumptions.assumptions:
            assumptions_text += f"• {a}\n"

    # Kick off flight search early if we have origin/destination
    # This might have been done in agent.start(), but if not, do it here
    if state.origin and state.destination:
        # Try to extract year/month from constraints or date_context
        flight_date_ctx = (
            state.constraints.month_or_season if state.constraints else None
        )
        # We're inside generate_plan (non-streaming), so we don't have date_context variable available directly unless we call get_current_date_context()
        if not flight_date_ctx:
            flight_date_ctx = None

        # We aren't capturing the result here, just ensuring the future is submitted
        # in case it wasn't already. The agent.get_flight_costs() will retrieve it.
        from app.agent.flight_search import search_flight_costs

        # Note: Ideally this should be async or managed by the agent class,
        # but this is a stateless helper. We'll rely on the agent's pre-computation.
        fc = search_flight_costs(state.origin, state.destination, flight_date_ctx)
        if fc:
            search_results.append(fc)

    _append_train_research(state, search_results, train_costs)

    # Kick off hotel search if destination is known (sync fallback)
    if state.destination:
        # Extract context if possible
        date_ctx = state.constraints.month_or_season if state.constraints else None
        budget = state.constraints.budget if state.constraints else None
        preferences = (
            " ".join(state.constraints.interests)
            if state.constraints and state.constraints.interests
            else None
        )

        from app.agent.hotel_search import search_hotel_costs

        hc = search_hotel_costs(state.destination, date_ctx, budget, preferences)
        if hc:
            search_results.append(hc)

    interests_text = ""
    if user_interests:
        interests_text = "\n\nUser's interests:\n" + "\n".join(user_interests)

    budget_currency = detect_budget_currency(state)

    plan_prompt = f"""Create a structured day-by-day itinerary based on this information:

{constraints_text}{assumptions_text}{interests_text}

Research findings (use these for accurate cost estimates):
{planning_research}

CURRENCY: ALL prices MUST be in {budget_currency}."""

    plan_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": plan_prompt},
    ]

    plan = client.chat_structured(plan_messages, TravelPlan, temperature=0.7)
    plan = enrich_plan_with_trust_metadata(
        plan,
        search_results,
        default_origin=state.origin,
        default_destination=state.destination,
    )
    state.current_plan = plan
    state.phase = Phase.REFINEMENT

    response = format_plan(plan)
    response += "\n\n---\nWant me to tweak anything? I can make it safer, faster, more comfortable, or change the base location. Or if you're happy with it, we're done!"

    state.add_message("assistant", response)
    return response


def generate_plan_stream(
    client: "AIClient",
    state: ConversationState,
    search_results: list[str],
    user_interests: list[str],
    on_tool_call: Callable[[str, dict], None] | None = None,
    language_code: str | None = None,
    flight_costs: str = "",
    hotel_costs: str = "",
    train_costs: dict | None = None,
) -> Iterator[str]:
    """Generate the travel itinerary with token streaming."""
    # FIX 1: Only do expensive research if we have NO prior search results
    # from the feasibility phase. This saves 5-15s of blocking time.
    # FIX 1: Only do expensive research if we have NO prior search results
    # from the feasibility phase. This saves 5-15s of blocking time.
    if not search_results:
        planning_research = _gather_planning_research(
            client,
            state,
            search_results,
            user_interests,
            on_tool_call=on_tool_call,
            language_code=language_code,
        )
        search_results.append(planning_research)
    if flight_costs and flight_costs not in search_results:
        search_results.append(flight_costs)
    if hotel_costs and hotel_costs not in search_results:
        search_results.append(hotel_costs)
    _append_train_research(state, search_results, train_costs)

    vibe = state.vibe or (state.constraints.vibe if state.constraints else None)
    system_prompt = get_phase_prompt("planning", language_code, vibe=vibe)
    constraints_text = format_constraints(state)
    assumptions_text = ""
    if state.assumptions:
        assumptions_text = "\n\nConfirmed Assumptions:\n"
        for a in state.assumptions.assumptions:
            assumptions_text += f"• {a}\n"

    interests_text = ""
    if user_interests:
        interests_text = "\n\nUser's interests:\n" + "\n".join(user_interests)

    budget_currency = detect_budget_currency(state)

    # Combine all prior research into the prompt
    research_context = (
        "\n\n".join(search_results[-5:])
        if search_results
        else "No prior research available."
    )

    plan_prompt = f"""Create a detailed day-by-day itinerary based on this information:

{constraints_text}{assumptions_text}{interests_text}

Research findings (use these for accurate cost estimates):
{research_context}

{flight_costs}

{hotel_costs}

CURRENCY: ALL prices MUST be in {budget_currency}.

FORMAT RULES (follow this EXACTLY):

1. Start with an H1 title like "# 5-Day Itinerary for [Destination] Adventure"

2. For each day use this format:
## Day X: [Title]
**Morning:** Activity description. Estimated cost: {budget_currency}X.
**Noon/Afternoon/Evening:** Continue with specific activities.
- Use **bold** for specific venue/restaurant names
- Include estimated cost for EACH activity
- Include specific timings where possible (e.g., "9:00 AM – 11:00 AM")

**Tips:**
- 2-4 practical tips per day (money-saving hacks, must-try food, hidden gems, important warnings)

**Day X total:** Accommodation {budget_currency}X + Food {budget_currency}X + Activities {budget_currency}X + Transport {budget_currency}X = {budget_currency}X

3. After all days, include:
## Budget Breakdown
- List each day's total
- Show Total Spending
- Show Budget Left (if under budget)

## General Tips for Your Trip
- Visa/entry requirements
- SIM card / connectivity advice
- Cultural etiquette
- Essential apps to download
- Money exchange tips
- Packing essentials for the season

QUALITY RULES:
- Recommend SPECIFIC named hotels with neighborhood and per-night cost
- Recommend SPECIFIC named restaurants for meals (not generic "lunch at a café")
- Include realistic transport between locations with mode and cost
- Every activity must have a cost estimate
- Be concise but specific — 1-2 lines per activity, not paragraphs
- Do NOT list generic "Breakfast", "Lunch", "Dinner" unless it's a famous food spot
- Focus on specific places, things to do, and unique experiences
- Do NOT include "Bookable Flight Options", "Bookable Stay Options", or "Sources Used" sections in this text.
- Booking links and sources are rendered in dedicated UI cards; avoid duplicate links in narrative."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": plan_prompt},
    ]

    full_response = ""
    # Stream tokens to the client in real-time
    for token in client.chat_stream(messages, temperature=0.7, max_tokens=5000):
        full_response += token
        yield token

    try:
        parsed_plan = _parse_plan_from_text(
            client,
            full_response,
            research_context,
        )
        parsed_plan = enrich_plan_with_trust_metadata(
            parsed_plan,
            search_results,
            default_origin=state.origin,
            default_destination=state.destination,
        )
        state.current_plan = parsed_plan
    except Exception:
        logger.exception("Synchronous plan structuring failed after streaming")

    state.phase = Phase.REFINEMENT

    extra = "\n\n---\nWant me to tweak anything? I can make it safer, faster, more comfortable, or change the base location. Or if you're happy with it, we're done!"
    yield extra
    full_response += extra
    state.add_message("assistant", full_response)
