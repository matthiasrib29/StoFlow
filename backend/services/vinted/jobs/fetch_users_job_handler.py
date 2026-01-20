"""
Fetch Users Job Handler - Récupération des utilisateurs Vinted pour prospection

This handler iterates through the alphabet to search for Vinted users,
filters them by country and item count, and saves them as prospects.

Author: Claude
Date: 2026-01-19
"""

import asyncio
from typing import Any, List

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from models.public.vinted_prospect import VintedProspect
from services.plugin_websocket_helper import PluginWebSocketHelper, PluginHTTPError
from shared.database import get_db_context
from shared.logging import get_logger
from .base_job_handler import BaseJobHandler

logger = get_logger(__name__)


# Search configuration
SEARCH_CHARS = list("abcdefghijklmnopqrstuvwxyz")
DELAY_BETWEEN_REQUESTS = 2.5  # seconds
DEFAULT_MAX_PAGES_PER_SEARCH = 50
DEFAULT_MIN_ITEMS = 200
DEFAULT_COUNTRY_CODE = "FR"
PER_PAGE = 100


class FetchUsersJobHandler(BaseJobHandler):
    """
    Handler for fetching Vinted users for prospection.

    Iterates through alphabet characters, searches for users,
    filters by country (FR) and item count (200+), saves to vinted_prospects table.
    """

    ACTION_CODE = "fetch_users"

    def create_tasks(self, job: MarketplaceJob) -> List[str]:
        """
        Define task steps for user fetching.

        Returns a task for each search character (A-Z).
        """
        return [f"Search users: '{char.upper()}'" for char in SEARCH_CHARS]

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute user fetching by iterating through alphabet.

        Args:
            job: MarketplaceJob with optional params:
                - min_items: Minimum items count (default: 200)
                - country_code: Country filter (default: FR)
                - max_pages_per_search: Max pages per character (default: 50)

        Returns:
            dict: {
                "success": bool,
                "total_found": int,
                "total_saved": int,
                "duplicates_skipped": int,
                "errors": int
            }
        """
        try:
            # Get parameters from job
            params = job.params or {}
            min_items = params.get("min_items", DEFAULT_MIN_ITEMS)
            country_code = params.get("country_code", DEFAULT_COUNTRY_CODE)
            max_pages = params.get("max_pages_per_search", DEFAULT_MAX_PAGES_PER_SEARCH)

            self.log_start(f"Fetching users (min_items={min_items}, country={country_code})")

            total_found = 0
            total_saved = 0
            duplicates_skipped = 0
            errors = 0

            # Use public DB session for saving prospects
            with get_db_context() as public_db:
                for char in SEARCH_CHARS:
                    self.log_debug(f"Searching users with '{char}'...")

                    for page in range(1, max_pages + 1):
                        try:
                            users = await self._fetch_users_page(char, page)

                            if not users:
                                self.log_debug(f"No more users for '{char}' at page {page}")
                                break

                            # Filter users
                            filtered = [
                                u for u in users
                                if u.get("country_iso_code") == country_code
                                and u.get("item_count", 0) >= min_items
                            ]

                            total_found += len(filtered)

                            # Save prospects
                            for user_data in filtered:
                                saved = self._save_prospect(public_db, user_data)
                                if saved:
                                    total_saved += 1
                                else:
                                    duplicates_skipped += 1

                            # Commit after each page
                            public_db.commit()

                            # Check if we got fewer results than requested (last page)
                            if len(users) < PER_PAGE:
                                break

                            # Rate limiting delay
                            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

                        except PluginHTTPError as e:
                            self.log_error(f"HTTP error fetching '{char}' page {page}: {e.status}")
                            errors += 1
                            # Continue with next page/char
                            await asyncio.sleep(DELAY_BETWEEN_REQUESTS * 2)  # Extra delay on error

                        except Exception as e:
                            self.log_error(f"Error fetching '{char}' page {page}: {e}", exc_info=True)
                            errors += 1

            result = {
                "success": True,
                "total_found": total_found,
                "total_saved": total_saved,
                "duplicates_skipped": duplicates_skipped,
                "errors": errors
            }

            self.log_success(
                f"Completed: {total_saved} saved, {duplicates_skipped} duplicates, {errors} errors"
            )
            return result

        except Exception as e:
            self.log_error(f"Fetch users failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _fetch_users_page(self, search_text: str, page: int) -> List[dict]:
        """
        Fetch a page of users from Vinted API.

        Args:
            search_text: Search character/text
            page: Page number

        Returns:
            List of user dicts from API response
        """
        result = await PluginWebSocketHelper.call_plugin(
            db=self.db,
            user_id=self.user_id,
            action="VINTED_FETCH_USERS",
            payload={
                "search_text": search_text,
                "page": page,
                "per_page": PER_PAGE
            },
            timeout=60,
            description=f"Fetch users '{search_text}' page {page}"
        )

        return result.get("users", [])

    def _save_prospect(self, db: Session, user_data: dict) -> bool:
        """
        Save a user as a prospect if not already exists.

        Args:
            db: Public database session
            user_data: User data from Vinted API

        Returns:
            True if saved, False if duplicate
        """
        vinted_user_id = user_data.get("id")
        if not vinted_user_id:
            return False

        # Check if already exists
        existing = db.query(VintedProspect).filter(
            VintedProspect.vinted_user_id == vinted_user_id
        ).first()

        if existing:
            return False

        # Create new prospect
        prospect = VintedProspect(
            vinted_user_id=vinted_user_id,
            login=user_data.get("login", "unknown"),
            country_code=user_data.get("country_iso_code"),
            item_count=user_data.get("item_count", 0),
            total_items_count=user_data.get("total_items_count", 0),
            feedback_count=user_data.get("feedback_count", 0),
            feedback_reputation=user_data.get("feedback_reputation"),
            is_business=user_data.get("business", False),
            profile_url=f"https://www.vinted.fr/member/{vinted_user_id}",
            status="new",
            created_by=self.user_id
        )

        db.add(prospect)
        return True
