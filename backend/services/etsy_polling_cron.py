"""
Etsy Polling Cron Job Service

Service de polling automatique pour Etsy (alternative aux webhooks).

Ce service s'exécute en arrière-plan et poll régulièrement l'API Etsy pour:
- Nouvelles commandes (toutes les 5 minutes)
- Listings mis à jour (toutes les 15 minutes)
- Stock faible (toutes les 15 minutes)

Architecture:
- APScheduler pour les tâches planifiées
- Isolation par utilisateur (poll tous les utilisateurs connectés à Etsy)
- Logs structurés pour monitoring
- Gestion d'erreurs robuste

Usage:
    # Démarrer le cron job
    python -m services.etsy_polling_cron

    # Ou importer et démarrer
    from services.etsy_polling_cron import start_etsy_polling_scheduler
    scheduler = start_etsy_polling_scheduler()

Author: Claude
Date: 2025-12-10
"""

import os
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models.public.platform_mapping import PlatformMapping
from services.etsy.etsy_polling_service import EtsyPollingService
from shared.config import settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Database Session Setup
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ========== CONFIGURATION ==========

# Intervalles de polling (en minutes)
POLL_INTERVAL_ORDERS = int(os.getenv("ETSY_POLLING_INTERVAL_ORDERS", "5"))
POLL_INTERVAL_LISTINGS = int(os.getenv("ETSY_POLLING_INTERVAL_LISTINGS", "15"))
POLL_INTERVAL_STOCK = 15  # Même interval que listings

# Seuil de stock faible
LOW_STOCK_THRESHOLD = int(os.getenv("ETSY_POLLING_LOW_STOCK_THRESHOLD", "5"))


# ========== HELPER FUNCTIONS ==========


def get_etsy_connected_users(db: Session) -> List[PlatformMapping]:
    """
    Récupère tous les utilisateurs connectés à Etsy.

    Args:
        db: Session de base de données

    Returns:
        Liste des PlatformMapping pour Etsy avec tokens valides
    """
    now = datetime.now(timezone.utc)

    # Query tous les utilisateurs Etsy avec access token non expiré
    mappings = (
        db.query(PlatformMapping)
        .filter(
            PlatformMapping.platform == "etsy",
            PlatformMapping.access_token.isnot(None),
            PlatformMapping.access_token_expires_at > now,
        )
        .all()
    )

    return mappings


# ========== POLLING TASKS ==========


def poll_new_orders_for_all_users():
    """
    Poll les nouvelles commandes Etsy pour tous les utilisateurs.

    Cette tâche s'exécute toutes les POLL_INTERVAL_ORDERS minutes.
    """
    logger.info("🔄 Starting Etsy polling: NEW ORDERS")
    db = SessionLocal()

    try:
        users = get_etsy_connected_users(db)
        logger.info(f"Found {len(users)} Etsy-connected users")

        total_new_orders = 0

        for mapping in users:
            try:
                # Créer service de polling pour cet utilisateur
                polling_service = EtsyPollingService(db, mapping.user_id)

                # Poll new receipts
                new_orders = polling_service.poll_new_receipts(
                    interval_minutes=POLL_INTERVAL_ORDERS
                )

                if new_orders:
                    logger.info(
                        f"✅ User {mapping.user_id} (shop: {mapping.shop_name}): "
                        f"{len(new_orders)} new orders"
                    )
                    total_new_orders += len(new_orders)

                    # TODO: Ici, envoyer notifications/webhooks à l'utilisateur
                    # - Email notification
                    # - Push notification
                    # - Webhook vers frontend

            except Exception as e:
                logger.error(
                    f"❌ Error polling orders for user {mapping.user_id}: {e}",
                    exc_info=True,
                )
                continue

        logger.info(
            f"✅ Etsy order polling completed: {total_new_orders} total new orders"
        )

    except Exception as e:
        logger.error(f"❌ Fatal error in order polling task: {e}", exc_info=True)

    finally:
        db.close()


def poll_updated_listings_for_all_users():
    """
    Poll les listings mis à jour Etsy pour tous les utilisateurs.

    Cette tâche s'exécute toutes les POLL_INTERVAL_LISTINGS minutes.
    """
    logger.info("🔄 Starting Etsy polling: UPDATED LISTINGS")
    db = SessionLocal()

    try:
        users = get_etsy_connected_users(db)
        logger.info(f"Found {len(users)} Etsy-connected users")

        total_updated = 0

        for mapping in users:
            try:
                polling_service = EtsyPollingService(db, mapping.user_id)

                # Poll updated listings
                updated_listings = polling_service.poll_updated_listings(
                    interval_minutes=POLL_INTERVAL_LISTINGS
                )

                if updated_listings:
                    logger.info(
                        f"✅ User {mapping.user_id} (shop: {mapping.shop_name}): "
                        f"{len(updated_listings)} updated listings"
                    )
                    total_updated += len(updated_listings)

                    # TODO: Sync listings to local DB
                    # - Update product status if sold
                    # - Sync stock quantity
                    # - Update price if changed

            except Exception as e:
                logger.error(
                    f"❌ Error polling listings for user {mapping.user_id}: {e}",
                    exc_info=True,
                )
                continue

        logger.info(
            f"✅ Etsy listing polling completed: {total_updated} total updates"
        )

    except Exception as e:
        logger.error(f"❌ Fatal error in listing polling task: {e}", exc_info=True)

    finally:
        db.close()


def poll_low_stock_for_all_users():
    """
    Poll les listings avec stock faible pour tous les utilisateurs.

    Cette tâche s'exécute toutes les POLL_INTERVAL_STOCK minutes.
    """
    logger.info("🔄 Starting Etsy polling: LOW STOCK")
    db = SessionLocal()

    try:
        users = get_etsy_connected_users(db)
        logger.info(f"Found {len(users)} Etsy-connected users")

        total_low_stock = 0

        for mapping in users:
            try:
                polling_service = EtsyPollingService(db, mapping.user_id)

                # Poll low stock listings
                low_stock_listings = polling_service.poll_low_stock_listings(
                    threshold=LOW_STOCK_THRESHOLD
                )

                if low_stock_listings:
                    logger.warning(
                        f"⚠️  User {mapping.user_id} (shop: {mapping.shop_name}): "
                        f"{len(low_stock_listings)} low stock listings"
                    )
                    total_low_stock += len(low_stock_listings)

                    # TODO: Envoyer alerte stock faible
                    # - Email alert
                    # - Dashboard notification

            except Exception as e:
                logger.error(
                    f"❌ Error polling stock for user {mapping.user_id}: {e}",
                    exc_info=True,
                )
                continue

        if total_low_stock > 0:
            logger.warning(
                f"⚠️  Etsy stock polling completed: {total_low_stock} total low stock items"
            )
        else:
            logger.info("✅ Etsy stock polling completed: No low stock items")

    except Exception as e:
        logger.error(f"❌ Fatal error in stock polling task: {e}", exc_info=True)

    finally:
        db.close()


# ========== SCHEDULER SETUP ==========


def start_etsy_polling_scheduler() -> BackgroundScheduler:
    """
    Démarre le scheduler de polling Etsy.

    Returns:
        BackgroundScheduler instance

    Example:
        >>> scheduler = start_etsy_polling_scheduler()
        >>> # Keep running...
        >>> time.sleep(3600)
        >>> scheduler.shutdown()
    """
    scheduler = BackgroundScheduler(timezone="UTC")

    # Job 1: Poll new orders (every 5 minutes)
    scheduler.add_job(
        func=poll_new_orders_for_all_users,
        trigger=IntervalTrigger(minutes=POLL_INTERVAL_ORDERS),
        id="etsy_poll_orders",
        name="Etsy Poll New Orders",
        replace_existing=True,
    )

    # Job 2: Poll updated listings (every 15 minutes)
    scheduler.add_job(
        func=poll_updated_listings_for_all_users,
        trigger=IntervalTrigger(minutes=POLL_INTERVAL_LISTINGS),
        id="etsy_poll_listings",
        name="Etsy Poll Updated Listings",
        replace_existing=True,
    )

    # Job 3: Poll low stock (every 15 minutes)
    scheduler.add_job(
        func=poll_low_stock_for_all_users,
        trigger=IntervalTrigger(minutes=POLL_INTERVAL_STOCK),
        id="etsy_poll_stock",
        name="Etsy Poll Low Stock",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("✅ Etsy polling scheduler started")
    logger.info(f"📋 Jobs configured:")
    logger.info(f"  - New Orders: every {POLL_INTERVAL_ORDERS} minutes")
    logger.info(f"  - Updated Listings: every {POLL_INTERVAL_LISTINGS} minutes")
    logger.info(f"  - Low Stock: every {POLL_INTERVAL_STOCK} minutes")

    return scheduler


def stop_etsy_polling_scheduler(scheduler: BackgroundScheduler):
    """
    Arrête le scheduler de polling Etsy.

    Args:
        scheduler: Instance du scheduler à arrêter
    """
    scheduler.shutdown(wait=True)
    logger.info("🛑 Etsy polling scheduler stopped")


# ========== MAIN (CLI) ==========


if __name__ == "__main__":
    """
    Point d'entrée CLI pour exécuter le cron job en standalone.

    Usage:
        python -m services.etsy_polling_cron
    """
    logger.info("=" * 80)
    logger.info("ETSY POLLING CRON JOB - STARTING")
    logger.info("=" * 80)

    # Start scheduler
    scheduler = start_etsy_polling_scheduler()

    try:
        # Keep running
        logger.info("🚀 Etsy polling service is running. Press Ctrl+C to stop.")

        while True:
            time.sleep(60)  # Sleep 1 minute
            # Log heartbeat every 10 minutes
            if int(time.time()) % 600 == 0:
                logger.info("💓 Etsy polling service heartbeat - still running")

    except (KeyboardInterrupt, SystemExit):
        logger.info("⚠️  Shutdown signal received")
        stop_etsy_polling_scheduler(scheduler)
        logger.info("👋 Etsy polling service stopped gracefully")
