"""
Vinted Pro Seller Service

Service for managing Vinted professional sellers (business accounts).
Provides CRUD operations and upsert from API data.

Author: Claude
Date: 2026-01-27
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from models.public.vinted_pro_seller import VintedProSeller
from services.vinted.vinted_contact_extractor import VintedContactExtractor
from shared.logging import get_logger

logger = get_logger(__name__)


class VintedProSellerService:
    """
    Service for Vinted pro seller CRUD and upsert operations.
    """

    @staticmethod
    def upsert_from_api(
        db: Session,
        user_data: dict,
        marketplace: str = "vinted_fr",
        created_by: Optional[int] = None,
    ) -> Tuple[VintedProSeller, bool]:
        """
        Insert or update a pro seller from Vinted API data.

        Args:
            db: Database session (public schema)
            user_data: Raw user data from Vinted API
            marketplace: Marketplace identifier
            created_by: Admin user ID who triggered the scan

        Returns:
            Tuple of (VintedProSeller, is_new)
        """
        vinted_user_id = user_data.get("id")
        if not vinted_user_id:
            raise ValueError("user_data must contain 'id'")

        # Check if exists
        existing = db.query(VintedProSeller).filter(
            VintedProSeller.vinted_user_id == vinted_user_id
        ).first()

        is_new = existing is None

        # Extract contact info from about text
        about = user_data.get("about", "")
        contacts = VintedContactExtractor.extract_all(about)

        # Extract business account info
        business_account = user_data.get("business_account") or {}

        # Map fields
        seller_data = {
            "login": user_data.get("login", "unknown"),
            "country_code": user_data.get("country_iso_code"),
            "country_id": user_data.get("country_id"),
            "country_title": user_data.get("country_title"),
            # Stats
            "item_count": user_data.get("item_count", 0),
            "total_items_count": user_data.get("total_items_count", 0),
            "given_item_count": user_data.get("given_item_count", 0),
            "taken_item_count": user_data.get("taken_item_count", 0),
            "followers_count": user_data.get("followers_count", 0),
            "following_count": user_data.get("following_count", 0),
            "feedback_count": user_data.get("feedback_count", 0),
            "feedback_reputation": user_data.get("feedback_reputation"),
            "positive_feedback_count": user_data.get("positive_feedback_count", 0),
            "neutral_feedback_count": user_data.get("neutral_feedback_count", 0),
            "negative_feedback_count": user_data.get("negative_feedback_count", 0),
            "is_on_holiday": user_data.get("is_on_holiday", False),
            # Business account
            "business_account_id": business_account.get("id"),
            "business_name": business_account.get("business_name"),
            "legal_name": business_account.get("legal_name"),
            "legal_code": business_account.get("legal_code"),
            "entity_type": business_account.get("entity_type"),
            "entity_type_title": business_account.get("entity_type_title"),
            "nationality": business_account.get("nationality"),
            "business_country": business_account.get("country"),
            "business_city": business_account.get("city"),
            "verified_identity": business_account.get("verified_identity"),
            "business_is_active": business_account.get("is_active"),
            # Profile
            "about": about or None,
            "profile_url": f"https://www.vinted.fr/member/{vinted_user_id}",
            "last_loged_on_ts": user_data.get("last_loged_on_ts"),
            # Extracted contacts
            "contact_email": contacts["email"],
            "contact_instagram": contacts["instagram"],
            "contact_tiktok": contacts["tiktok"],
            "contact_youtube": contacts["youtube"],
            "contact_website": contacts["website"],
            "contact_phone": contacts["phone"],
            # Metadata
            "marketplace": marketplace,
            "last_scanned_at": datetime.now(timezone.utc),
        }

        if existing:
            # Update existing seller
            for key, value in seller_data.items():
                if value is not None:
                    setattr(existing, key, value)
            db.flush()
            return existing, False
        else:
            # Create new seller
            seller = VintedProSeller(
                vinted_user_id=vinted_user_id,
                created_by=created_by,
                **seller_data,
            )
            db.add(seller)
            db.flush()
            return seller, True

    @staticmethod
    def list_sellers(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        country_code: Optional[str] = None,
        marketplace: Optional[str] = None,
        min_items: Optional[int] = None,
        search: Optional[str] = None,
        has_email: Optional[bool] = None,
        has_instagram: Optional[bool] = None,
    ) -> Tuple[List[VintedProSeller], int]:
        """
        List pro sellers with filtering and pagination.

        Args:
            db: Database session (public)
            skip: Offset
            limit: Max results
            status: Filter by status
            country_code: Filter by country
            marketplace: Filter by marketplace
            min_items: Filter by minimum item count
            search: Search in login or business_name
            has_email: Filter sellers with/without email
            has_instagram: Filter sellers with/without instagram

        Returns:
            Tuple of (list of sellers, total count)
        """
        query = db.query(VintedProSeller)

        if status:
            query = query.filter(VintedProSeller.status == status)
        if country_code:
            query = query.filter(VintedProSeller.country_code == country_code)
        if marketplace:
            query = query.filter(VintedProSeller.marketplace == marketplace)
        if min_items is not None:
            query = query.filter(VintedProSeller.item_count >= min_items)
        if search:
            query = query.filter(
                or_(
                    VintedProSeller.login.ilike(f"%{search}%"),
                    VintedProSeller.business_name.ilike(f"%{search}%"),
                )
            )
        if has_email is not None:
            if has_email:
                query = query.filter(VintedProSeller.contact_email.isnot(None))
            else:
                query = query.filter(VintedProSeller.contact_email.is_(None))
        if has_instagram is not None:
            if has_instagram:
                query = query.filter(VintedProSeller.contact_instagram.isnot(None))
            else:
                query = query.filter(VintedProSeller.contact_instagram.is_(None))

        total = query.count()

        sellers = query.order_by(
            VintedProSeller.item_count.desc()
        ).offset(skip).limit(limit).all()

        return sellers, total

    @staticmethod
    def get_seller(db: Session, seller_id: int) -> Optional[VintedProSeller]:
        """Get a pro seller by ID."""
        return db.query(VintedProSeller).filter(
            VintedProSeller.id == seller_id
        ).first()

    @staticmethod
    def get_stats(db: Session) -> dict:
        """
        Get pro seller statistics.

        Returns:
            Dict with total, by_status, by_country, by_marketplace,
            with_email, with_instagram, with_any_contact
        """
        total = db.query(VintedProSeller).count()

        # By status
        status_counts = db.query(
            VintedProSeller.status,
            func.count(VintedProSeller.id)
        ).group_by(VintedProSeller.status).all()
        by_status = {s: c for s, c in status_counts}

        # By country
        country_counts = db.query(
            VintedProSeller.country_code,
            func.count(VintedProSeller.id)
        ).group_by(VintedProSeller.country_code).all()
        by_country = {country or "unknown": count for country, count in country_counts}

        # By marketplace
        marketplace_counts = db.query(
            VintedProSeller.marketplace,
            func.count(VintedProSeller.id)
        ).group_by(VintedProSeller.marketplace).all()
        by_marketplace = {m: c for m, c in marketplace_counts}

        # Contact counts
        with_email = db.query(VintedProSeller).filter(
            VintedProSeller.contact_email.isnot(None)
        ).count()

        with_instagram = db.query(VintedProSeller).filter(
            VintedProSeller.contact_instagram.isnot(None)
        ).count()

        with_any_contact = db.query(VintedProSeller).filter(
            or_(
                VintedProSeller.contact_email.isnot(None),
                VintedProSeller.contact_instagram.isnot(None),
                VintedProSeller.contact_tiktok.isnot(None),
                VintedProSeller.contact_youtube.isnot(None),
                VintedProSeller.contact_website.isnot(None),
                VintedProSeller.contact_phone.isnot(None),
            )
        ).count()

        return {
            "total_sellers": total,
            "by_status": by_status,
            "by_country": by_country,
            "by_marketplace": by_marketplace,
            "with_email": with_email,
            "with_instagram": with_instagram,
            "with_any_contact": with_any_contact,
        }

    @staticmethod
    def update_seller(
        db: Session,
        seller_id: int,
        status: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[VintedProSeller]:
        """Update a pro seller's status and/or notes."""
        seller = VintedProSellerService.get_seller(db, seller_id)
        if not seller:
            return None

        if status:
            seller.status = status
            if status == "contacted" and not seller.contacted_at:
                seller.contacted_at = datetime.now(timezone.utc)

        if notes is not None:
            seller.notes = notes

        db.commit()
        db.refresh(seller)
        return seller

    @staticmethod
    def bulk_update_status(
        db: Session,
        seller_ids: List[int],
        status: str,
    ) -> int:
        """Bulk update status for multiple sellers."""
        update_data = {"status": status}
        if status == "contacted":
            update_data["contacted_at"] = datetime.now(timezone.utc)

        result = db.query(VintedProSeller).filter(
            VintedProSeller.id.in_(seller_ids)
        ).update(update_data, synchronize_session=False)

        db.commit()
        return result

    @staticmethod
    def delete_seller(db: Session, seller_id: int) -> bool:
        """Delete a pro seller."""
        seller = VintedProSellerService.get_seller(db, seller_id)
        if not seller:
            return False

        db.delete(seller)
        db.commit()
        return True
