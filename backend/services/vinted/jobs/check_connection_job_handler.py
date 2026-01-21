"""
Check Connection Job Handler - Verify Vinted connection status

Calls GET /api/v2/users/current via WebSocket/Plugin to verify
the user is connected to Vinted and update VintedConnection.

Author: Claude
Date: 2026-01-21
"""

from datetime import datetime, timezone
from typing import Any, List

from models.user.marketplace_job import MarketplaceJob
from models.user.vinted_connection import VintedConnection
from services.vinted.jobs.base_job_handler import BaseJobHandler


class CheckConnectionJobHandler(BaseJobHandler):
    """
    Handler for checking Vinted connection status.

    This handler:
    1. Calls GET /api/v2/users/current via WebSocket (plugin)
    2. Creates or updates VintedConnection based on result
    3. Returns connection status with user info

    Unlike other handlers, this doesn't require a product_id.
    """

    ACTION_CODE = "check_connection"

    def create_tasks(self, job: MarketplaceJob) -> List[str]:
        """Create task list for check connection workflow."""
        return [
            "Check Vinted session",
            "Update connection status"
        ]

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute connection check.

        Args:
            job: MarketplaceJob (product_id not required for this action)

        Returns:
            dict: {
                "success": bool,
                "connected": bool,
                "vinted_user_id": int | None,
                "login": str | None,
                "error": str | None
            }
        """
        self.log_start("Checking Vinted connection status")

        try:
            # 1. Call GET /api/v2/users/current via plugin
            result = await self.call_plugin(
                http_method="GET",
                path="/api/v2/users/current",
                timeout=30,
                description="Check Vinted connection"
            )

            # 2. Handle plugin response
            if not result.get("success"):
                error_msg = result.get("error", "Plugin call failed")
                self.log_error(f"Plugin call failed: {error_msg}")

                # Mark as disconnected if plugin fails
                self._update_connection_status(connected=False)

                return {
                    "success": False,
                    "connected": False,
                    "vinted_user_id": None,
                    "login": None,
                    "error": error_msg
                }

            # 3. Parse user data from response
            user_data = result.get("data", {})
            vinted_user_id = user_data.get("id")
            login = user_data.get("login")

            if not vinted_user_id or not login:
                self.log_error("Missing required fields (id, login) in response")
                return {
                    "success": False,
                    "connected": False,
                    "vinted_user_id": None,
                    "login": None,
                    "error": "Invalid response: missing user id or login"
                }

            # 4. Update VintedConnection
            connection = self._update_connection_status(
                connected=True,
                vinted_user_id=int(vinted_user_id),
                login=login,
                user_data=user_data
            )

            self.log_success(f"Connected as {login} (Vinted ID: {vinted_user_id})")

            return {
                "success": True,
                "connected": True,
                "vinted_user_id": connection.vinted_user_id,
                "login": connection.username,
                "error": None
            }

        except Exception as e:
            self.log_error(f"Check connection failed: {e}", exc_info=True)
            return {
                "success": False,
                "connected": False,
                "vinted_user_id": None,
                "login": None,
                "error": str(e)
            }

    def _update_connection_status(
        self,
        connected: bool,
        vinted_user_id: int | None = None,
        login: str | None = None,
        user_data: dict | None = None
    ) -> VintedConnection | None:
        """
        Create or update VintedConnection.

        Args:
            connected: Whether user is connected
            vinted_user_id: Vinted user ID (if connected)
            login: Vinted username (if connected)
            user_data: Full user data from API (for stats)

        Returns:
            VintedConnection instance (or None if disconnected and no existing connection)
        """
        now = datetime.now(timezone.utc)

        # Find existing connection
        connection = self.db.query(VintedConnection).filter(
            VintedConnection.user_id == self.user_id
        ).first()

        if connected:
            if connection:
                # Update existing connection
                connection.connect(vinted_user_id=vinted_user_id, username=login)
            else:
                # Create new connection
                connection = VintedConnection(
                    user_id=self.user_id,
                    vinted_user_id=vinted_user_id,
                    username=login,
                    is_connected=True,
                    created_at=now,
                    last_synced_at=now
                )
                self.db.add(connection)

            # Update seller stats if available
            if user_data:
                connection.update_seller_stats(user_data)

            self.db.commit()
            return connection
        else:
            # Mark as disconnected if exists
            if connection:
                connection.disconnect()
                self.db.commit()
            return connection
