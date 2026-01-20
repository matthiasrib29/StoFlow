"""
Admin Stats Service

Service for aggregating statistics for admin dashboard.
Provides KPIs, subscription distribution, and registration trends.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, and_, case
from sqlalchemy.orm import Session

from models.public.user import User, UserRole, SubscriptionTier
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# MRR estimates per tier (EUR/month)
TIER_PRICES = {
    SubscriptionTier.FREE: 0,
    SubscriptionTier.STARTER: 9.99,
    SubscriptionTier.PRO: 29.99,
    SubscriptionTier.ENTERPRISE: 99.99,
}


class AdminStatsService:
    """Service for admin dashboard statistics."""

    @staticmethod
    def get_overview(db: Session) -> dict:
        """
        Get overview statistics for admin dashboard.

        Returns:
            dict with total_users, active_users, inactive_users, locked_users
        """
        # Get user counts by status
        total = db.query(func.count(User.id)).scalar() or 0
        active = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
        inactive = db.query(func.count(User.id)).filter(User.is_active == False).scalar() or 0
        locked = db.query(func.count(User.id)).filter(User.locked_until.isnot(None)).scalar() or 0

        # Count by role
        admins = db.query(func.count(User.id)).filter(User.role == UserRole.ADMIN).scalar() or 0
        users = db.query(func.count(User.id)).filter(User.role == UserRole.USER).scalar() or 0
        support = db.query(func.count(User.id)).filter(User.role == UserRole.SUPPORT).scalar() or 0

        logger.debug(f"Admin stats overview: total={total}, active={active}, inactive={inactive}")

        return {
            "total_users": total,
            "active_users": active,
            "inactive_users": inactive,
            "locked_users": locked,
            "users_by_role": {
                "admin": admins,
                "user": users,
                "support": support,
            },
        }

    @staticmethod
    def get_subscriptions(db: Session) -> dict:
        """
        Get subscription distribution and estimated MRR.

        Returns:
            dict with users_by_tier, total_mrr, active_subscriptions
        """
        # Count users by subscription tier (only active users)
        tier_counts = (
            db.query(User.subscription_tier, func.count(User.id))
            .filter(User.is_active == True)
            .group_by(User.subscription_tier)
            .all()
        )

        users_by_tier = {
            "free": 0,
            "starter": 0,
            "pro": 0,
            "enterprise": 0,
        }

        total_mrr = 0.0

        for tier, count in tier_counts:
            tier_key = tier.value if hasattr(tier, 'value') else str(tier)
            users_by_tier[tier_key] = count

            # Calculate MRR contribution
            tier_enum = SubscriptionTier(tier_key) if isinstance(tier_key, str) else tier
            tier_price = TIER_PRICES.get(tier_enum, 0)
            total_mrr += count * tier_price

        # Count paying subscribers (non-free)
        paying_subscribers = sum(
            count for tier, count in tier_counts
            if (tier.value if hasattr(tier, 'value') else str(tier)) != "free"
        )

        logger.debug(f"Admin stats subscriptions: mrr={total_mrr:.2f}, paying={paying_subscribers}")

        return {
            "users_by_tier": users_by_tier,
            "total_mrr": round(total_mrr, 2),
            "paying_subscribers": paying_subscribers,
            "active_subscriptions": sum(users_by_tier.values()),
        }

    @staticmethod
    def get_registrations(
        db: Session,
        period: str = "month",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Get daily registration counts for a period.

        Args:
            db: SQLAlchemy session
            period: 'week', 'month', or '3months'
            start_date: Optional custom start date
            end_date: Optional custom end date

        Returns:
            dict with period, data (list of {date, count})
        """
        now = datetime.now(timezone.utc)

        # Determine date range
        if start_date and end_date:
            date_from = start_date
            date_to = end_date
        elif period == "week":
            date_from = now - timedelta(days=7)
            date_to = now
        elif period == "3months":
            date_from = now - timedelta(days=90)
            date_to = now
        else:  # default: month
            date_from = now - timedelta(days=30)
            date_to = now

        # Query daily registrations
        registrations = (
            db.query(
                func.date(User.created_at).label("date"),
                func.count(User.id).label("count"),
            )
            .filter(
                and_(
                    User.created_at >= date_from,
                    User.created_at <= date_to,
                )
            )
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at))
            .all()
        )

        # Convert to list of dicts
        data = [
            {
                "date": str(row.date),
                "count": row.count,
            }
            for row in registrations
        ]

        # Fill missing days with 0
        data_dict = {item["date"]: item["count"] for item in data}
        filled_data = []
        current_date = date_from.date()
        end = date_to.date()

        while current_date <= end:
            date_str = str(current_date)
            filled_data.append({
                "date": date_str,
                "count": data_dict.get(date_str, 0),
            })
            current_date += timedelta(days=1)

        # Calculate totals
        total_registrations = sum(item["count"] for item in filled_data)
        avg_per_day = round(total_registrations / max(len(filled_data), 1), 2)

        logger.debug(f"Admin stats registrations: period={period}, total={total_registrations}")

        return {
            "period": period,
            "start_date": str(date_from.date()),
            "end_date": str(date_to.date()),
            "data": filled_data,
            "total": total_registrations,
            "average_per_day": avg_per_day,
        }

    @staticmethod
    def get_recent_activity(db: Session, limit: int = 10) -> dict:
        """
        Get recent user activity (last logins, new registrations).

        Args:
            db: SQLAlchemy session
            limit: Maximum number of entries

        Returns:
            dict with recent_logins, new_registrations
        """
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        # Recent logins (last 24h)
        recent_logins = (
            db.query(User)
            .filter(
                and_(
                    User.last_login.isnot(None),
                    User.last_login >= last_24h,
                )
            )
            .order_by(User.last_login.desc())
            .limit(limit)
            .all()
        )

        # New registrations (last 7 days)
        new_registrations = (
            db.query(User)
            .filter(User.created_at >= last_7d)
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )

        logger.debug(f"Admin recent activity: logins={len(recent_logins)}, new={len(new_registrations)}")

        return {
            "recent_logins": [
                {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                }
                for user in recent_logins
            ],
            "new_registrations": [
                {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "subscription_tier": user.subscription_tier.value if hasattr(user.subscription_tier, 'value') else str(user.subscription_tier),
                }
                for user in new_registrations
            ],
        }
