"""Formatting utilities for travel agent output."""

from app.agent.models import BudgetBreakdown, ConversationState, RiskAssessment, TravelPlan


def format_constraints(state: ConversationState) -> str:
    """Format constraints for prompts.

    Args:
        state: Current conversation state.

    Returns:
        Formatted constraints string.
    """
    c = state.constraints
    if not c:
        return f"From: {state.origin}\nTo: {state.destination}"

    lines = [f"From: {c.origin}", f"To: {c.destination}"]
    if c.month_or_season:
        lines.append(f"Season/Month: {c.month_or_season}")
    if c.duration_days:
        lines.append(f"Duration: {c.duration_days} days")
    if c.solo_or_group:
        lines.append(f"Travel type: {c.solo_or_group}")
    if c.budget:
        lines.append(f"Budget: {c.budget}")
    if c.interests:
        lines.append(f"Interests: {', '.join(c.interests)}")
    return "\n".join(lines)


def format_risk_assessment(risk: RiskAssessment) -> str:
    """Format risk assessment as a friendly, conversational summary.

    Args:
        risk: Risk assessment to format.

    Returns:
        Formatted risk assessment string.
    """
    lines = [risk.friendly_summary]

    if risk.warnings:
        lines.append("")
        for warning in risk.warnings:
            lines.append(f"Heads up: {warning}")

    if risk.alternatives:
        lines.append("")
        for alt in risk.alternatives:
            lines.append(f"Alternative: {alt}")

    return "\n".join(lines)


def format_plan(plan: TravelPlan) -> str:
    """Format travel plan for display — concise and scannable.

    Args:
        plan: Travel plan to format.

    Returns:
        Formatted plan string.
    """
    lines = [f"**{plan.summary}**"]
    lines.append(f"Route: {plan.route}")

    if plan.acclimatization_notes:
        lines.append(f"Note: {plan.acclimatization_notes}")

    lines.append("\n---\n")

    for day in plan.days:
        lines.append(f"**Day {day.day}: {day.title}**")

        for activity in day.activities:
            cost_str = (
                f" — {activity.cost_estimate}" if activity.cost_estimate else ""
            )
            notes_str = f"  ({activity.cost_notes})" if activity.cost_notes else ""
            lines.append(f"  - {activity.activity}{cost_str}{notes_str}")

        if day.travel_time:
            travel_cost = f" ({day.travel_cost})" if day.travel_cost else ""
            lines.append(f"  Travel: {day.travel_time}{travel_cost}")

        if day.accommodation:
            acc_cost = (
                f" — {day.accommodation_cost}/night"
                if day.accommodation_cost
                else ""
            )
            lines.append(f"  Stay: {day.accommodation}{acc_cost}")

        if day.meals_cost:
            lines.append(f"  Meals: ~{day.meals_cost}")

        if day.day_total:
            lines.append(f"  Day total: {day.day_total}")

        if day.notes:
            lines.append(f"  ⚠ {day.notes}")

        # Display tips for this day
        if day.tips:
            lines.append("  Tips:")
            for tip in day.tips:
                lines.append(f"    → {tip}")

        lines.append("")

    # Budget breakdown
    if plan.budget_breakdown:
        b = plan.budget_breakdown
        lines.append("---\n")
        lines.append("**Budget Breakdown**\n")
        lines.append(f"  Flights: {b.flights}")
        lines.append(f"  Accommodation: {b.accommodation}")
        lines.append(f"  Transport: {b.local_transport}")
        lines.append(f"  Meals: {b.meals}")
        lines.append(f"  Activities: {b.activities}")
        lines.append(f"  Misc: {b.miscellaneous}")
        lines.append(f"  **Total: {b.total}**")
        if b.notes:
            lines.append(f"\n{b.notes}")

    # General trip tips
    if plan.general_tips:
        lines.append("\n---\n")
        lines.append("**Tips & Good to Know**\n")
        for tip in plan.general_tips:
            lines.append(f"  • {tip}")

    return "\n".join(lines)
