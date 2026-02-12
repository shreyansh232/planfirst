"""Feasibility phase handler."""

from datetime import datetime
from typing import TYPE_CHECKING, Callable

from app.agent.formatters import format_constraints
from app.agent.models import ConversationState, Phase, RiskAssessment
from app.agent.prompts import get_phase_prompt
from app.agent.tools import TOOL_DEFINITIONS, execute_tool
from app.agent.utils import get_current_date_context

if TYPE_CHECKING:
    from app.agent.ai_client import AIClient


def run_feasibility_check(
    client: "AIClient",
    state: ConversationState,
    search_results: list[str],
    on_tool_call: Callable[[str, dict], None] | None = None,
    language_code: str | None = None,
) -> tuple[str, bool]:
    """Run feasibility check and return risk assessment.

    Args:
        client: AI client instance.
        state: Conversation state to update.
        search_results: List to append search results to.
        on_tool_call: Optional callback for tool calls.

    Returns:
        Tuple of (response text, has_high_risk).
    """
    from app.agent.formatters import format_risk_assessment

    system_prompt = get_phase_prompt("feasibility", language_code)
    constraints_text = format_constraints(state)

    # First, gather current information via web search
    date_context = get_current_date_context()
    search_prompt = f"""You need to evaluate the feasibility of this trip:

{date_context}

{constraints_text}

Before providing your assessment, search for current information about:
1. Current travel advisories or restrictions for the destination
2. Weather/seasonal conditions for the specified travel period
3. Any recent infrastructure or accessibility issues

IMPORTANT: Use the CURRENT YEAR ({datetime.now().year}) in your search queries, not past years.

Use the web_search tool to gather this information, then provide your risk assessment."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": search_prompt},
    ]

    # Use chat with tools to gather current information
    search_response = client.chat_with_tools(
        messages=messages,
        tools=TOOL_DEFINITIONS,
        tool_executor=execute_tool,
        temperature=0.3,
        max_tool_calls=2,
        on_tool_call=on_tool_call,
    )

    # Store search context for later phases
    search_results.append(search_response)

    # Now get structured risk assessment with the gathered information
    assessment_prompt = f"""Based on the information gathered, provide a structured risk assessment for this trip:

{constraints_text}

Research findings:
{search_response}

Provide a risk assessment for each category."""

    assessment_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": assessment_prompt},
    ]

    risk = client.chat_structured(assessment_messages, RiskAssessment, temperature=0.3)
    state.risk_assessment = risk

    # Format response
    response = format_risk_assessment(risk)

    has_high_risk = any(
        [
            risk.season_weather.value == "HIGH",
            risk.route_accessibility.value == "HIGH",
            risk.altitude_health.value == "HIGH",
            risk.infrastructure.value == "HIGH",
        ]
    )

    if has_high_risk:
        response += "\n\nThis trip has some real risks. Want to go ahead anyway, or should we look at alternatives?"
        state.awaiting_confirmation = True
    else:
        # Auto-proceed to assumptions if no high risk
        state.phase = Phase.ASSUMPTIONS

    state.add_message("assistant", response)
    return response, has_high_risk
