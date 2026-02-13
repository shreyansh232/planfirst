"""Flight cost search using DuckDuckGo.

Searches for average flight costs between origin and destination
to provide a baseline estimate for the planning phase.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime

from ddgs import DDGS

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1)


def search_flight_costs(
    origin: str, destination: str, date_context: str | None = None
) -> str:
    """Search for estimated flight costs.

    Args:
        origin: Origin city/airport.
        destination: Destination city/airport.
        date_context: Month/season/dates of travel.

    Returns:
        Summary string of search results constraints cost info.
    """
    try:
        current_year = datetime.now().year
        date_str = date_context if date_context else f"{current_year}"
        query = f"round trip flight cost from {origin} to {destination} {date_str} price"
        logger.info(f"[FLIGHT SEARCH] Searching: {query}")

        def _run() -> list[dict]:
            with DDGS() as ddgs:
                # Text search for costs
                return list(ddgs.text(query, max_results=4))

        future = _executor.submit(_run)
        results = future.result(timeout=6)

        if not results:
            return ""

        # Format results into a context string
        snippets = []
        for r in results:
            title = r.get("title", "")
            body = r.get("body", "")
            snippets.append(f"- {title}: {body}")

        summary = "\n".join(snippets)
        logger.info(f"[FLIGHT SEARCH] Found {len(results)} results")
        return f"Flight Cost Estimates Research ({origin} -> {destination}):\n{summary}"

    except FuturesTimeoutError:
        logger.warning("[FLIGHT SEARCH] Timeout")
        return ""
    except Exception as e:
        logger.error(f"[FLIGHT SEARCH] Error: {e}")
        return ""
