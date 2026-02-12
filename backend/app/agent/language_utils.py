"""Language detection and preference management utilities."""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserPreference

logger = logging.getLogger(__name__)


# Common language codes mapped from detected languages
LANGUAGE_CODES = {
    "english": "en",
    "french": "fr",
    "spanish": "es",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "dutch": "nl",
    "russian": "ru",
    "chinese": "zh",
    "japanese": "ja",
    "korean": "ko",
    "arabic": "ar",
    "hindi": "hi",
    "turkish": "tr",
    "polish": "pl",
    "swedish": "sv",
    "norwegian": "no",
    "danish": "da",
    "finnish": "fi",
}


async def get_user_language(db: AsyncSession, user_id: UUID) -> Optional[str]:
    """Get the user's preferred language from their preferences.

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        Language code (e.g., 'en', 'fr') or None if not set
    """
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    pref = result.scalar_one_or_none()
    return pref.preferred_language if pref else None


async def update_user_language(
    db: AsyncSession,
    user_id: UUID,
    language_code: str,
) -> None:
    """Update or create user's preferred language.

    Args:
        db: Database session
        user_id: User's UUID
        language_code: Language code (e.g., 'en', 'fr')
    """
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    pref = result.scalar_one_or_none()

    if pref:
        pref.preferred_language = language_code
    else:
        pref = UserPreference(
            user_id=user_id,
            preferred_language=language_code,
        )
        db.add(pref)

    await db.commit()
    logger.info(f"Updated preferred language for user {user_id}: {language_code}")


def get_language_instruction(language_code: Optional[str]) -> str:
    """Get the language instruction for the system prompt.

    Args:
        language_code: Language code (e.g., 'en', 'fr')

    Returns:
        Language instruction string for the system prompt
    """
    if not language_code:
        return ""

    language_names = {
        "en": "English",
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "nl": "Dutch",
        "ru": "Russian",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ar": "Arabic",
        "hi": "Hindi",
        "tr": "Turkish",
        "pl": "Polish",
        "sv": "Swedish",
        "no": "Norwegian",
        "da": "Danish",
        "fi": "Finnish",
    }

    lang_name = language_names.get(language_code, language_code)
    return f"\n\nLANGUAGE PREFERENCE: The user prefers to communicate in {lang_name} ({language_code}). ALL your responses MUST be in {lang_name}."
