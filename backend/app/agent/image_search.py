"""Destination image search using DuckDuckGo Images.

Searches for famous landmarks/places at a destination and returns
thumbnail URLs for use in the frontend carousel.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from ddgs import DDGS

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1)


def search_destination_images(
    destination: str, num_images: int = 6
) -> list[dict[str, str]]:
    """Search for images of famous places at a destination.

    Args:
        destination: The travel destination (e.g., "France", "Tokyo").
        num_images: Number of images to return (default 6).

    Returns:
        List of dicts with keys: title, image_url, thumbnail_url, source.
        Returns empty list on failure.
    """
    try:
        query = f"{destination} famous landmarks tourist places"
        logger.info(f"[IMAGE SEARCH] Searching images for: {query}")

        def _run() -> list[dict]:
            with DDGS() as ddgs:
                return list(ddgs.images(query, max_results=num_images * 2 + 5))

        # Run with timeout to avoid blocking
        future = _executor.submit(_run)
        
        # Increased timeout to 10s and max_time to ensure results
        raw_results = future.result(timeout=10)

        images = []
        domain_counts = {}
        
        for r in raw_results:
            image_url = r.get("image", "")
            thumbnail_url = r.get("thumbnail", "")
            title = r.get("title", "")
            page_url = r.get("url", "")
            source = r.get("source", "Web")  # This is often 'Bing'

            # Skip if no URLs
            if not image_url or not thumbnail_url:
                continue

            # Extract domain from the actual page URL, not the source field
            domain = "unknown"
            if page_url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(page_url).netloc.replace("www.", "")
                except:
                    pass
            
            # Allow up to 2 images per domain, but prefer variety
            if domain_counts.get(domain, 0) >= 2:
                continue
            
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

            # Clean the title (remove " - Wikipedia" etc.)
            for suffix in [" — Wikipédia", " - Wikipedia", " | Britannica", " - Tripadvisor", " - Holidify", " : Chronicles of ..."]:
                if title.endswith(suffix):
                    title = title[: -len(suffix)]
            
            # Remove "Top 10" type prefixes if possible? 
            # Often titles are "Top 10 places in X". 
            # Let's just keep the title as is for now, maybe strip common junk.

            images.append(
                {
                    "title": title.strip(),
                    "image_url": image_url,
                    "thumbnail_url": thumbnail_url,
                    "source": page_url, # Pass the full page URL as source so frontend can display domain
                }
            )

            if len(images) >= num_images:
                break

        logger.info(f"[IMAGE SEARCH] Found {len(images)} images for: {destination}")
        return images

    except FuturesTimeoutError:
        logger.warning(f"[IMAGE SEARCH] Timeout searching images for: {destination}")
        return []
    except Exception as e:
        logger.error(f"[IMAGE SEARCH] Error searching images for {destination}: {e}")
        return []
