"""
Message Job Handler - Synchronisation des conversations/messages Vinted

Gère la synchronisation via le système de jobs:
- Sync inbox (liste des conversations)
- Sync conversation spécifique (messages)

Usage:
- Sans conversation_id: sync l'inbox (toutes les conversations)
- Avec conversation_id dans result_data: sync une conversation spécifique

Author: Claude
Date: 2025-12-19
"""

import time
from typing import Any

from sqlalchemy.orm import Session

from models.user.vinted_job import VintedJob
from .base_job_handler import BaseJobHandler


class MessageJobHandler(BaseJobHandler):
    """
    Handler pour la synchronisation des conversations Vinted.

    Modes de fonctionnement:
    - Sync inbox: job.result_data = None ou {}
    - Sync conversation: job.result_data = {"conversation_id": int}
    - Sync all pages: job.result_data = {"sync_all": true}
    """

    ACTION_CODE = "message"

    def __init__(
        self,
        db: Session,
        shop_id: int | None = None,
        job_id: int | None = None
    ):
        super().__init__(db, shop_id, job_id)
        self._conversation_service = None

    @property
    def conversation_service(self):
        """Lazy-load conversation service."""
        if self._conversation_service is None:
            from services.vinted.vinted_conversation_service import (
                VintedConversationService
            )
            self._conversation_service = VintedConversationService()
        return self._conversation_service

    async def execute(self, job: VintedJob) -> dict[str, Any]:
        """
        Synchronise les conversations/messages depuis Vinted.

        Args:
            job: VintedJob avec result_data optionnel:
                - {} ou None: sync l'inbox (liste conversations)
                - {"conversation_id": int}: sync une conversation
                - {"sync_all": bool}: sync toutes les pages de l'inbox
                - {"page": int, "per_page": int}: pagination

        Returns:
            dict: {
                "success": bool,
                "mode": "inbox" | "conversation",
                "synced": int,
                "created": int,
                "updated": int,
                "error": str | None
            }
        """
        start_time = time.time()

        # Extract parameters from job
        params = job.result_data if isinstance(job.result_data, dict) else {}
        conversation_id = params.get('conversation_id')

        try:
            if conversation_id:
                return await self._sync_conversation(conversation_id, start_time)
            else:
                return await self._sync_inbox(params, start_time)

        except Exception as e:
            elapsed = time.time() - start_time
            self.log_error(f"Erreur sync messages: {e} ({elapsed:.1f}s)", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _sync_inbox(
        self,
        params: dict,
        start_time: float
    ) -> dict[str, Any]:
        """Sync l'inbox (liste des conversations)."""
        page = params.get('page', 1)
        per_page = params.get('per_page', 20)
        sync_all = params.get('sync_all', False)

        self.log_start(
            f"Synchronisation inbox (page={page}, sync_all={sync_all})"
        )

        result = await self.conversation_service.sync_inbox(
            self.db,
            page=page,
            per_page=per_page,
            sync_all_pages=sync_all
        )

        elapsed = time.time() - start_time
        synced = result.get('synced', 0)
        created = result.get('created', 0)
        updated = result.get('updated', 0)
        unread = result.get('unread', 0)

        self.log_success(
            f"{synced} conversations sync ({created} new, {updated} updated, "
            f"{unread} unread) ({elapsed:.1f}s)"
        )

        return {
            "success": True,
            "mode": "inbox",
            **result
        }

    async def _sync_conversation(
        self,
        conversation_id: int,
        start_time: float
    ) -> dict[str, Any]:
        """Sync une conversation spécifique (ses messages)."""
        self.log_start(f"Synchronisation conversation #{conversation_id}")

        result = await self.conversation_service.sync_conversation(
            self.db, conversation_id
        )

        elapsed = time.time() - start_time
        messages_synced = result.get('messages_synced', 0)
        messages_new = result.get('messages_new', 0)

        self.log_success(
            f"Conversation #{conversation_id}: {messages_synced} messages "
            f"({messages_new} new) ({elapsed:.1f}s)"
        )

        return {
            "success": True,
            "mode": "conversation",
            **result
        }
