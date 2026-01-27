"""
Vinted Contact Extractor

Utility class to extract contact information (email, Instagram, TikTok,
YouTube, website, phone) from Vinted user 'about' text using regex patterns.

Author: Claude
Date: 2026-01-27
"""

import re
from typing import Optional


class VintedContactExtractor:
    """
    Extract contact information from Vinted user 'about' field.

    All methods are static and return None if no match is found.
    """

    # --- Email ---
    _EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE,
    )

    # --- Instagram ---
    # Matches: instagram.com/xxx, insta:xxx, ig:xxx, @xxx (only if near instagram context)
    _INSTAGRAM_URL_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9_.]+)",
        re.IGNORECASE,
    )
    _INSTAGRAM_HANDLE_PATTERN = re.compile(
        r"(?:insta(?:gram)?|ig)\s*[:=@/]\s*@?([a-zA-Z0-9_.]+)",
        re.IGNORECASE,
    )

    # --- TikTok ---
    _TIKTOK_URL_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?tiktok\.com/@?([a-zA-Z0-9_.]+)",
        re.IGNORECASE,
    )
    _TIKTOK_HANDLE_PATTERN = re.compile(
        r"tiktok\s*[:=@/]\s*@?([a-zA-Z0-9_.]+)",
        re.IGNORECASE,
    )

    # --- YouTube ---
    _YOUTUBE_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?youtube\.com/(?:@|channel/|c/)([a-zA-Z0-9_\-]+)",
        re.IGNORECASE,
    )

    # --- Website ---
    # Matches https?:// URLs excluding known social media domains
    _WEBSITE_PATTERN = re.compile(
        r"https?://[^\s<>\"']+",
        re.IGNORECASE,
    )
    _EXCLUDED_DOMAINS = {
        "vinted.fr", "vinted.com", "vinted.de", "vinted.es", "vinted.it",
        "vinted.nl", "vinted.be", "vinted.pl", "vinted.pt", "vinted.cz",
        "vinted.lt", "vinted.lu", "vinted.at", "vinted.co.uk",
        "instagram.com", "tiktok.com", "youtube.com", "youtu.be",
        "facebook.com", "fb.com", "twitter.com", "x.com",
    }

    # --- Phone (French format) ---
    # Matches: +33 X XX XX XX XX, 06 XX XX XX XX, 07 XX XX XX XX
    _PHONE_PATTERN = re.compile(
        r"(?:\+33\s*[67]|0[67])[\s.\-]?\d{2}[\s.\-]?\d{2}[\s.\-]?\d{2}[\s.\-]?\d{2}",
        re.IGNORECASE,
    )

    @staticmethod
    def extract_all(about_text: Optional[str]) -> dict:
        """
        Extract all contact information from about text.

        Args:
            about_text: Raw bio/about text from Vinted profile

        Returns:
            Dict with keys: email, instagram, tiktok, youtube, website, phone.
            Values are None if not found.
        """
        if not about_text or not about_text.strip():
            return {
                "email": None,
                "instagram": None,
                "tiktok": None,
                "youtube": None,
                "website": None,
                "phone": None,
            }

        return {
            "email": VintedContactExtractor.extract_email(about_text),
            "instagram": VintedContactExtractor.extract_instagram(about_text),
            "tiktok": VintedContactExtractor.extract_tiktok(about_text),
            "youtube": VintedContactExtractor.extract_youtube(about_text),
            "website": VintedContactExtractor.extract_website(about_text),
            "phone": VintedContactExtractor.extract_phone(about_text),
        }

    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """Extract first email address from text."""
        match = VintedContactExtractor._EMAIL_PATTERN.search(text)
        return match.group(0).lower() if match else None

    @staticmethod
    def extract_instagram(text: str) -> Optional[str]:
        """Extract Instagram handle from text."""
        # Try URL first
        match = VintedContactExtractor._INSTAGRAM_URL_PATTERN.search(text)
        if match:
            return match.group(1)

        # Try handle patterns (insta:xxx, ig:xxx)
        match = VintedContactExtractor._INSTAGRAM_HANDLE_PATTERN.search(text)
        if match:
            return match.group(1)

        return None

    @staticmethod
    def extract_tiktok(text: str) -> Optional[str]:
        """Extract TikTok handle from text."""
        match = VintedContactExtractor._TIKTOK_URL_PATTERN.search(text)
        if match:
            return match.group(1)

        match = VintedContactExtractor._TIKTOK_HANDLE_PATTERN.search(text)
        if match:
            return match.group(1)

        return None

    @staticmethod
    def extract_youtube(text: str) -> Optional[str]:
        """Extract YouTube channel from text."""
        match = VintedContactExtractor._YOUTUBE_PATTERN.search(text)
        return match.group(1) if match else None

    @staticmethod
    def extract_website(text: str) -> Optional[str]:
        """Extract website URL, excluding known social media domains."""
        matches = VintedContactExtractor._WEBSITE_PATTERN.findall(text)
        for url in matches:
            # Check if domain is excluded
            url_lower = url.lower()
            is_excluded = any(
                domain in url_lower
                for domain in VintedContactExtractor._EXCLUDED_DOMAINS
            )
            if not is_excluded:
                # Clean trailing punctuation
                url = url.rstrip(".,;:!?)")
                return url
        return None

    @staticmethod
    def extract_phone(text: str) -> Optional[str]:
        """Extract French phone number from text."""
        match = VintedContactExtractor._PHONE_PATTERN.search(text)
        if match:
            # Normalize: remove spaces, dots, dashes
            phone = re.sub(r"[\s.\-]", "", match.group(0))
            return phone
        return None
