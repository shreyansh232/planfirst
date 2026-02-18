"""Source attribution and confidence scoring helpers for itinerary output."""

from __future__ import annotations

import re
from urllib.parse import quote_plus, urlparse

from app.agent.models import (
    ConfidenceBreakdown,
    PlanConfidence,
    SourceAttribution,
    TravelPlan,
)

_URL_PATTERN = re.compile(r"https?://[^\s\])\"'>,;]+")
_BAD_URL_TOKENS = (
    "example.com",
    "localhost",
    "127.0.0.1",
    "<",
    ">",
    "{",
    "}",
    "...",
    "notfound",
    "n/a",
)
_TRAIN_NUMBER_PATTERN = re.compile(r"\b\d{5}\b")
_MULTISPACE_PATTERN = re.compile(r"\s+")
_PRICE_DIGIT_PATTERN = re.compile(r"^\d[\d,]*(?:\.\d+)?$")


def _clean_fragment(value: str | None) -> str:
    if not value:
        return ""
    return _MULTISPACE_PATTERN.sub(" ", value).strip()


def _infer_source_type(domain: str) -> str:
    lowered = domain.lower()
    if any(k in lowered for k in ("booking", "agoda", "airbnb", "expedia", "hotel")):
        return "lodging"
    if any(k in lowered for k in ("skyscanner", "kayak", "flight", "airline")):
        return "flight"
    if any(k in lowered for k in ("gov", "travel.state", "cdc", "who.int")):
        return "advisory"
    if any(k in lowered for k in ("weather", "met", "accuweather")):
        return "weather"
    return "general"


def _is_http_url(url: str) -> bool:
    if not url:
        return False
    lowered = url.lower()
    if any(token in lowered for token in _BAD_URL_TOKENS):
        return False
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _flight_search_deeplink(route: str, airline: str | None = None) -> str:
    query = " ".join(
        part
        for part in [_clean_fragment(route), _clean_fragment(airline), "flight booking"]
        if part
    )
    return f"https://www.google.com/travel/flights?q={quote_plus(query)}"


def _stay_search_deeplink(
    name: str,
    location: str | None = None,
    destination: str | None = None,
) -> str:
    query = " ".join(
        part
        for part in [
            _clean_fragment(name),
            _clean_fragment(location),
            _clean_fragment(destination),
            "hotel booking",
        ]
        if part
    )
    return f"https://www.booking.com/searchresults.html?ss={quote_plus(query)}"


def _train_search_deeplink(
    route: str,
    train_name: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
) -> str:
    query = " ".join(
        part
        for part in [
            _clean_fragment(origin),
            _clean_fragment(destination),
            _clean_fragment(route),
            _clean_fragment(train_name),
            "IRCTC train booking",
        ]
        if part
    )
    return f"https://www.google.com/search?q={quote_plus(query)}"


def _normalize_train_name(train_name: str | None) -> str | None:
    """Drop unreliable train numbers/codes to avoid fake precision in UI."""
    cleaned = _clean_fragment(train_name)
    if not cleaned:
        return None

    cleaned = _TRAIN_NUMBER_PATTERN.sub("", cleaned)
    cleaned = _clean_fragment(cleaned.strip("-:|"))
    if not cleaned:
        return None

    tokens = cleaned.split()
    if not tokens:
        return None
    code_like_tokens = sum(1 for token in tokens if token.isupper() or len(token) <= 3)
    if len(tokens) >= 3 and (code_like_tokens / len(tokens)) >= 0.8:
        return None
    return cleaned


def _normalize_train_route(
    route: str | None,
    default_origin: str | None,
    default_destination: str | None,
) -> str:
    cleaned = _clean_fragment(route)
    if not cleaned and default_origin and default_destination:
        return f"{default_origin} to {default_destination}"
    if (
        default_origin
        and default_destination
        and (
            default_origin.lower() not in cleaned.lower()
            or default_destination.lower() not in cleaned.lower()
        )
    ):
        return f"{default_origin} to {default_destination}"
    return cleaned


def _normalize_price_text(price: str) -> str:
    cleaned = _clean_fragment(price)
    if _PRICE_DIGIT_PATTERN.fullmatch(cleaned):
        return f"₹{cleaned}"
    return cleaned


def _normalize_booking_links(
    plan: TravelPlan,
    default_origin: str | None = None,
    default_destination: str | None = None,
) -> None:
    """Force robust booking deeplinks so users avoid stale 404 pages."""
    for flight in plan.flights:
        deeplink = _flight_search_deeplink(flight.route, flight.airline)
        original = (flight.booking_url or "").strip()
        if _is_http_url(original) and original != deeplink:
            if not flight.notes:
                flight.notes = f"Original link provided: {original}"
        flight.booking_url = deeplink

    for stay in plan.lodgings:
        deeplink = _stay_search_deeplink(
            stay.name,
            stay.location,
            default_destination,
        )
        original = (stay.booking_url or "").strip()
        if _is_http_url(original) and original != deeplink:
            if not stay.notes:
                stay.notes = f"Original link provided: {original}"
        stay.booking_url = deeplink

    seen_train_keys: set[tuple[str, str, str]] = set()
    normalized_trains = []
    for train in plan.trains:
        train.route = _normalize_train_route(
            train.route,
            default_origin=default_origin,
            default_destination=default_destination,
        )
        train.train_name = _normalize_train_name(train.train_name)
        train.price = _normalize_price_text(train.price)
        deeplink = _train_search_deeplink(
            train.route,
            train.train_name,
            origin=default_origin,
            destination=default_destination,
        )
        original = _clean_fragment(train.booking_url)
        if _is_http_url(original) and original != deeplink:
            if not train.notes:
                train.notes = f"Original link provided: {original}"
        train.booking_url = deeplink

        train_key = (
            train.route.lower(),
            (train.train_class or "").strip().lower(),
            train.price.strip().lower(),
        )
        if train.route and train.price and train_key not in seen_train_keys:
            seen_train_keys.add(train_key)
            normalized_trains.append(train)

    plan.trains = normalized_trains[:4]


def extract_sources(
    search_results: list[str], limit: int = 8
) -> list[SourceAttribution]:
    """Extract unique sources from search/tool output strings."""
    seen: set[str] = set()
    sources: list[SourceAttribution] = []

    # Prefer the most recent research context.
    for block in reversed(search_results[-10:]):
        for raw_url in _URL_PATTERN.findall(block):
            normalized = raw_url.rstrip(".,)")
            if normalized in seen:
                continue
            parsed = urlparse(normalized)
            if not parsed.netloc:
                continue

            domain = parsed.netloc.replace("www.", "")
            sources.append(
                SourceAttribution(
                    url=normalized,
                    domain=domain,
                    source_type=_infer_source_type(domain),
                )
            )
            seen.add(normalized)

            if len(sources) >= limit:
                return sources
    return sources


def _score_source_coverage(source_count: int) -> int:
    if source_count <= 0:
        return 25
    return min(100, 30 + source_count * 12)


def _score_cost_completeness(plan: TravelPlan) -> int:
    total_activities = sum(len(day.activities) for day in plan.days)
    activities_with_cost = sum(
        1 for day in plan.days for activity in day.activities if activity.cost_estimate
    )

    activity_score = 40
    if total_activities > 0:
        activity_score = int((activities_with_cost / total_activities) * 100)

    days_with_totals = sum(1 for day in plan.days if day.day_total)
    day_total_score = (
        int((days_with_totals / len(plan.days)) * 100) if plan.days else 40
    )
    budget_score = 100 if plan.budget_breakdown else 50

    combined = int(activity_score * 0.55 + day_total_score * 0.25 + budget_score * 0.20)
    return max(0, min(100, combined))


def _score_itinerary_specificity(plan: TravelPlan) -> int:
    if not plan.days:
        return 30

    with_travel = sum(1 for day in plan.days if day.travel_time or day.travel_cost)
    with_stay = sum(1 for day in plan.days if day.accommodation)
    with_notes_or_tips = sum(1 for day in plan.days if day.notes or day.tips)

    travel_score = int((with_travel / len(plan.days)) * 100)
    stay_score = int((with_stay / len(plan.days)) * 100)
    tips_score = int((with_notes_or_tips / len(plan.days)) * 100)
    booking_score = 100 if (plan.flights or plan.lodgings) else 40

    combined = int(
        travel_score * 0.30
        + stay_score * 0.25
        + tips_score * 0.25
        + booking_score * 0.20
    )
    return max(0, min(100, combined))


def build_plan_confidence(plan: TravelPlan, source_count: int) -> PlanConfidence:
    """Generate an interpretable confidence score for a plan."""
    source_coverage = _score_source_coverage(source_count)
    cost_completeness = _score_cost_completeness(plan)
    itinerary_specificity = _score_itinerary_specificity(plan)

    score = int(
        source_coverage * 0.35 + cost_completeness * 0.40 + itinerary_specificity * 0.25
    )
    score = max(0, min(100, score))

    if score >= 80:
        level = "HIGH"
    elif score >= 60:
        level = "MEDIUM"
    else:
        level = "LOW"

    summary = (
        f"{level} confidence ({score}/100) based on source coverage, "
        "cost completeness, and itinerary specificity."
    )

    return PlanConfidence(
        score=score,
        level=level,
        summary=summary,
        breakdown=ConfidenceBreakdown(
            source_coverage=source_coverage,
            cost_completeness=cost_completeness,
            itinerary_specificity=itinerary_specificity,
        ),
    )


def enrich_plan_with_trust_metadata(
    plan: TravelPlan,
    search_results: list[str],
    default_origin: str | None = None,
    default_destination: str | None = None,
) -> TravelPlan:
    """Attach source attributions and confidence metadata to a travel plan."""
    _normalize_booking_links(
        plan,
        default_origin=default_origin,
        default_destination=default_destination,
    )

    if not plan.sources:
        plan.sources = extract_sources(search_results)

    plan.confidence = build_plan_confidence(plan, len(plan.sources))
    return plan
