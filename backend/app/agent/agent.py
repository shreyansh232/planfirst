"""TravelAgent - Main orchestrator for the travel planning conversation."""

import logging
from typing import Callable, Optional

from app.agent.ai_client import AIClient
from app.agent.models import ConversationState, Phase
from app.agent.phases import (
    assumptions,
    clarification,
    feasibility,
    planning,
    refinement,
)

logger = logging.getLogger(__name__)


class TravelAgent:
    """Orchestrates the constraint-first travel planning conversation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "google/gemini-3-flash-preview",
        on_search: Optional[Callable[[str], None]] = None,
    ):
        """Initialize the travel agent.

        Args:
            api_key: OpenRouter API key. Uses OPENROUTER_API_KEY env var if not provided.
            model: Model to use via OpenRouter.
            on_search: Optional callback when a web search is performed.
        """
        self.client = AIClient(api_key=api_key, model=model)
        self.state = ConversationState()
        self.on_search = on_search
        self.search_results: list[str] = []  # Store search results for context
        self.user_interests: list[str] = []  # Store user interests/adjustments
        self._initial_extraction = None

    def _handle_tool_call(self, tool_name: str, arguments: dict) -> None:
        """Handle tool call notifications."""
        if tool_name == "web_search" and self.on_search:
            query = arguments.get("query", "")
            self.on_search(query)

    def start(self, user_prompt: str) -> str:
        """Start a new travel planning conversation.

        Extracts everything possible from the initial prompt and only asks
        for what's still missing.

        Args:
            user_prompt: User's initial prompt (e.g., "Plan a trip from Mumbai to Japan in March, 7 days, solo").

        Returns:
            Clarification questions for missing info, or request for origin/destination.
        """
        response, extracted = clarification.handle_start(
            self.client, self.state, user_prompt
        )
        self._initial_extraction = extracted
        return response

    def process_clarification(self, answers: str) -> tuple[str, bool]:
        """Process user's answers to clarification questions.

        Merges answers with any info already extracted from the initial prompt.

        Args:
            answers: User's answers to the clarification questions.

        Returns:
            Tuple of (response text, has_high_risk).
        """
        constraints = clarification.process_clarification(
            self.client, self.state, answers, self._initial_extraction
        )
        self.state.constraints = constraints

        # Move to feasibility phase
        self.state.phase = Phase.FEASIBILITY
        return feasibility.run_feasibility_check(
            self.client,
            self.state,
            self.search_results,
            self._handle_tool_call,
        )

    def confirm_proceed(self, proceed: bool) -> str:
        """Handle user's decision to proceed despite high risk.

        Args:
            proceed: Whether user wants to proceed despite risks.

        Returns:
            Next phase response.
        """
        self.state.awaiting_confirmation = False

        if not proceed:
            return "Totally fair. You might want to check out the alternatives I mentioned, or we can adjust your dates/destination. What do you think?"

        self.state.phase = Phase.ASSUMPTIONS
        return self._generate_assumptions()

    def proceed_to_assumptions(self) -> str:
        """Move to assumptions phase after feasibility check."""
        self.state.phase = Phase.ASSUMPTIONS
        return self._generate_assumptions()

    def _generate_assumptions(self) -> str:
        """Generate and present assumptions before planning.

        Returns:
            Assumptions text for user confirmation.
        """
        return assumptions.generate_assumptions(self.client, self.state)

    def confirm_assumptions(
        self,
        confirmed: bool,
        adjustments: Optional[str] = None,
        modifications: Optional[str] = None,
        additional_interests: Optional[str] = None,
    ) -> str:
        """Handle user's confirmation of assumptions.

        Args:
            confirmed: Whether user confirms the assumptions.
            adjustments: Any adjustments the user wants to make (deprecated, use modifications).
            modifications: Any modifications the user wants to make.
            additional_interests: Additional interests to incorporate.

        Returns:
            Generated plan or request for clarification.
        """
        from app.agent.sanitizer import sanitize_input

        self.state.awaiting_confirmation = False

        # Use modifications if provided, otherwise use adjustments for backward compatibility
        user_modifications = modifications or adjustments
        if additional_interests:
            user_modifications = f"{user_modifications or ''}\nAdditional interests: {additional_interests}"

        if not confirmed and user_modifications:
            # Sanitize user modifications
            result = sanitize_input(user_modifications)
            user_modifications = result.text
            if result.injection_detected:
                logger.warning(
                    "Possible prompt injection in modifications: %s", result.flags
                )

            # Store user interests/adjustments for later use
            self.user_interests.append(user_modifications)
            if self.state.constraints:
                self.state.constraints.interests.append(user_modifications)

            self.state.add_message("user", f"Adjustments needed: {user_modifications}")

            # Search for events/activities based on user interests
            search_results = assumptions.search_for_interests(
                self.client, self.state, user_modifications, self._handle_tool_call
            )
            if search_results:
                self.search_results.append(search_results)

            # Update assumptions with modifications, then proceed directly to planning
            assumptions.update_assumptions_with_interests(
                self.client, self.state, user_modifications, self.search_results
            )

        # Proceed to planning (whether confirmed directly or after incorporating modifications)
        self.state.phase = Phase.PLANNING
        return self._generate_plan()

    def _generate_plan(self) -> str:
        """Generate the travel itinerary.

        Returns:
            Day-by-day travel plan.
        """
        return planning.generate_plan(
            self.client,
            self.state,
            self.search_results,
            self.user_interests,
            self._handle_tool_call,
        )

    def refine_plan(self, refinement_type: str) -> str:
        """Refine the plan based on user's choice.

        Args:
            refinement_type: Type of refinement requested.

        Returns:
            Refined plan.
        """
        return refinement.refine_plan(self.client, self.state, refinement_type)
