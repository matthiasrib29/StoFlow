"""
Vinted Prospect Service

Service for managing Vinted prospects for admin prospection feature.

Author: Claude
Date: 2026-01-19
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from models.public.vinted_prospect import VintedProspect
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedProspectService:
    """
    Service for Vinted prospect CRUD operations.
    """

    @staticmethod
    def list_prospects(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        country_code: Optional[str] = None,
        min_items: Optional[int] = None,
        is_business: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[VintedProspect], int]:
        """
        List prospects with filtering and pagination.

        Args:
            db: Database session (public)
            skip: Offset
            limit: Max results
            status: Filter by status (new, contacted, converted, ignored)
            country_code: Filter by country
            min_items: Filter by minimum item count
            is_business: Filter by business status
            search: Search in login

        Returns:
            Tuple of (list of prospects, total count)
        """
        query = db.query(VintedProspect)

        # Apply filters
        if status:
            query = query.filter(VintedProspect.status == status)
        if country_code:
            query = query.filter(VintedProspect.country_code == country_code)
        if min_items is not None:
            query = query.filter(VintedProspect.item_count >= min_items)
        if is_business is not None:
            query = query.filter(VintedProspect.is_business == is_business)
        if search:
            query = query.filter(
                VintedProspect.login.ilike(f"%{search}%")
            )

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        prospects = query.order_by(
            VintedProspect.item_count.desc()
        ).offset(skip).limit(limit).all()

        return prospects, total

    @staticmethod
    def get_prospect(db: Session, prospect_id: int) -> Optional[VintedProspect]:
        """
        Get a prospect by ID.

        Args:
            db: Database session
            prospect_id: Prospect ID

        Returns:
            VintedProspect or None
        """
        return db.query(VintedProspect).filter(
            VintedProspect.id == prospect_id
        ).first()

    @staticmethod
    def get_prospect_by_vinted_id(db: Session, vinted_user_id: int) -> Optional[VintedProspect]:
        """
        Get a prospect by Vinted user ID.

        Args:
            db: Database session
            vinted_user_id: Vinted user ID

        Returns:
            VintedProspect or None
        """
        return db.query(VintedProspect).filter(
            VintedProspect.vinted_user_id == vinted_user_id
        ).first()

    @staticmethod
    def update_prospect(
        db: Session,
        prospect_id: int,
        status: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[VintedProspect]:
        """
        Update a prospect.

        Args:
            db: Database session
            prospect_id: Prospect ID
            status: New status
            notes: New notes

        Returns:
            Updated prospect or None
        """
        prospect = VintedProspectService.get_prospect(db, prospect_id)
        if not prospect:
            return None

        if status:
            prospect.status = status
            # Set contacted_at when status changes to 'contacted'
            if status == "contacted" and not prospect.contacted_at:
                prospect.contacted_at = datetime.now(timezone.utc)

        if notes is not None:
            prospect.notes = notes

        db.commit()
        db.refresh(prospect)
        return prospect

    @staticmethod
    def bulk_update_status(
        db: Session,
        prospect_ids: List[int],
        status: str
    ) -> int:
        """
        Bulk update status for multiple prospects.

        Args:
            db: Database session
            prospect_ids: List of prospect IDs
            status: New status

        Returns:
            Number of updated records
        """
        update_data = {"status": status}
        if status == "contacted":
            update_data["contacted_at"] = datetime.now(timezone.utc)

        result = db.query(VintedProspect).filter(
            VintedProspect.id.in_(prospect_ids)
        ).update(update_data, synchronize_session=False)

        db.commit()
        return result

    @staticmethod
    def delete_prospect(db: Session, prospect_id: int) -> bool:
        """
        Delete a prospect.

        Args:
            db: Database session
            prospect_id: Prospect ID

        Returns:
            True if deleted, False if not found
        """
        prospect = VintedProspectService.get_prospect(db, prospect_id)
        if not prospect:
            return False

        db.delete(prospect)
        db.commit()
        return True

    @staticmethod
    def get_stats(db: Session) -> dict:
        """
        Get prospect statistics.

        Args:
            db: Database session

        Returns:
            Statistics dict
        """
        # Total count
        total = db.query(VintedProspect).count()

        # Count by status
        status_counts = db.query(
            VintedProspect.status,
            func.count(VintedProspect.id)
        ).group_by(VintedProspect.status).all()

        by_status = {status: count for status, count in status_counts}

        # Count by country
        country_counts = db.query(
            VintedProspect.country_code,
            func.count(VintedProspect.id)
        ).group_by(VintedProspect.country_code).all()

        by_country = {country or "unknown": count for country, count in country_counts}

        # Average item count
        avg_items_result = db.query(
            func.avg(VintedProspect.item_count)
        ).scalar()
        avg_items = float(avg_items_result) if avg_items_result else 0.0

        # Business count
        business_count = db.query(VintedProspect).filter(
            VintedProspect.is_business == True
        ).count()

        return {
            "total_prospects": total,
            "by_status": by_status,
            "by_country": by_country,
            "avg_item_count": round(avg_items, 2),
            "business_count": business_count
        }
