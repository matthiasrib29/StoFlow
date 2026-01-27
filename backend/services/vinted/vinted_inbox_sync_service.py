"""
Vinted Inbox Sync Service

Service dedicated to synchronizing conversations list from Vinted inbox.

Extracted from VintedConversationService for better separation of concerns.

Author: Claude
Date: 2026-01-06
"""

from datetime import datetime, timezone
from typing import Any

from dateutil.parser import parse as parse_datetime
from sqlalchemy.orm import Session

from repositories.vinted_conversation_repository import VintedConversationRepository
from services.plugin_websocket_helper import PluginWebSocketHelper  # WebSocket architecture (2026-01-12)
from shared.vinted import VintedConversationAPI, VintedReferers
from shared.logging import get_logger
from shared.config import settings

logger = get_logger(__name__)


class VintedInboxSyncService:
    """Service for syncing Vinted inbox (conversation list)."""

    def __init__(self, user_id: int | None = None):
        """
        Initialize service.

        Args:
            user_id: ID utilisateur (requis pour WebSocket) (2026-01-12)
        """
        self.user_id = user_id

    async def sync_inbox(
        self,
        db: Session,
        page: int = 1,
        per_page: int = 20,
        sync_all_pages: bool = False
    ) -> dict[str, Any]:
        """
        Sync conversations from Vinted inbox.

        Uses PluginTask to call GET /api/v2/inbox.

        Args:
            db: SQLAlchemy Session
            page: Page to fetch (1-indexed)
            per_page: Items per page (max 20)
            sync_all_pages: If True, fetch all pages until exhausted

        Returns:
            dict with:
            - synced: Number of conversations synced
            - created: Number of new conversations
            - updated: Number of updated conversations
            - total: Total conversations in inbox
            - unread: Number of unread conversations
        """
        result = {
            "synced": 0,
            "created": 0,
            "updated": 0,
            "total": 0,
            "unread": 0,
            "errors": []
        }

        try:
            current_page = page
            has_more = True

            while has_more:
                logger.info(f"[VintedInboxSyncService] Fetching inbox page {current_page}")

                # Call Vinted API via WebSocket (2026-01-12)
                api_result = await PluginWebSocketHelper.call_plugin_http(
                    db=db,
                    user_id=self.user_id,
                    http_method="GET",
                    path=VintedConversationAPI.get_inbox(page=current_page, per_page=per_page),
                    timeout=settings.plugin_timeout_sync,
                    description=f"Sync inbox page {current_page}"
                )

                if not api_result:
                    logger.error("[VintedInboxSyncService] No result from inbox API")
                    result["errors"].append(f"Page {current_page}: No API response")
                    break

                # Parse response
                conversations_data = api_result.get("conversations", [])
                pagination = api_result.get("pagination", {})

                result["total"] = pagination.get("total_entries", 0)

                # Process each conversation
                for conv_data in conversations_data:
                    try:
                        conv = self._parse_conversation(conv_data)
                        existing = VintedConversationRepository.get_by_id(
                            db, conv["conversation_id"]
                        )

                        if existing:
                            # Update existing
                            VintedConversationRepository.upsert(db, conv)
                            result["updated"] += 1
                        else:
                            # Create new
                            VintedConversationRepository.upsert(db, conv)
                            result["created"] += 1

                        result["synced"] += 1

                        if conv.get("is_unread"):
                            result["unread"] += 1

                    except (ValueError, KeyError, TypeError) as e:
                        conv_id = conv_data.get("id", "unknown")
                        logger.error(f"[VintedInboxSyncService] Error processing conv {conv_id}: {e}", exc_info=True)
                        result["errors"].append(f"Conv {conv_id}: {str(e)}")

                # Check if more pages
                total_pages = pagination.get("total_pages", 1)
                if sync_all_pages and current_page < total_pages:
                    current_page += 1
                else:
                    has_more = False

            logger.info(
                f"[VintedInboxSyncService] Inbox sync complete: "
                f"synced={result['synced']}, created={result['created']}, "
                f"updated={result['updated']}, unread={result['unread']}"
            )

            return result

        except Exception as e:
            logger.error(f"[VintedInboxSyncService] sync_inbox error: {e}", exc_info=True)
            # schema_translate_map survives rollback - no need to restore
            raise

    def _parse_conversation(self, data: dict) -> dict:
        """
        Parse conversation data from Vinted API response.

        Args:
            data: Raw conversation data from API

        Returns:
            dict ready for VintedConversation model
        """
        opposite_user = data.get("opposite_user", {})
        opposite_photo = opposite_user.get("photo", {}) or {}
        item_photos = data.get("item_photos", [])
        first_photo = item_photos[0] if item_photos else {}

        # Parse datetime
        updated_at_str = data.get("updated_at")
        updated_at_vinted = None
        if updated_at_str:
            try:
                updated_at_vinted = parse_datetime(updated_at_str)
            except (ValueError, TypeError):
                pass

        # Get thumbnail URL (100x100)
        photo_url = None
        thumbnails = opposite_photo.get("thumbnails", [])
        for thumb in thumbnails:
            if thumb.get("type") == "thumb100":
                photo_url = thumb.get("url")
                break
        if not photo_url:
            photo_url = opposite_photo.get("url")

        # Get item photo URL
        item_photo_url = None
        item_thumbnails = first_photo.get("thumbnails", [])
        for thumb in item_thumbnails:
            if thumb.get("type") == "thumb150x210":
                item_photo_url = thumb.get("url")
                break
        if not item_photo_url:
            item_photo_url = first_photo.get("url")

        return {
            "conversation_id": data.get("id"),
            "opposite_user_id": opposite_user.get("id"),
            "opposite_user_login": opposite_user.get("login"),
            "opposite_user_photo_url": photo_url,
            "last_message_preview": data.get("description"),
            "is_unread": data.get("unread", False),
            "unread_count": 1 if data.get("unread") else 0,
            "item_count": data.get("item_count", 1),
            "item_id": first_photo.get("id") if first_photo else None,
            "item_title": data.get("description"),
            "item_photo_url": item_photo_url,
            "updated_at_vinted": updated_at_vinted,
            "last_synced_at": datetime.now(timezone.utc),
        }


__all__ = ["VintedInboxSyncService"]
