"""
Migrate existing OAuth tokens from plaintext to encrypted.

This script:
1. Finds all eBay and Etsy credentials with plaintext tokens
2. Encrypts them using the encryption service
3. Stores encrypted versions in *_encrypted columns
4. Clears plaintext columns

Security: Phase 1.1 (2026-01-12)

Usage:
    python scripts/migrate_oauth_tokens_encryption.py

Author: Claude
Date: 2026-01-12
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text
from models.user.ebay_credentials import EbayCredentials
from models.user.etsy_credentials import EtsyCredentials
from shared.database import SessionLocal, get_db_context
from shared.encryption import get_encryption_service
from shared.logging import get_logger

logger = get_logger(__name__)


def get_user_schemas(db):
    """Get all user_* schemas."""
    result = db.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def migrate_ebay_tokens(db, schema: str):
    """Migrate eBay tokens for a specific schema."""
    # Use schema_translate_map for ORM queries (survives commit/rollback)
    db = db.execution_options(schema_translate_map={"tenant": schema})

    # Get credentials with plaintext tokens
    credentials = db.execute(
        select(EbayCredentials).where(
            EbayCredentials.access_token.isnot(None),
            EbayCredentials.access_token_encrypted.is_(None)
        )
    ).scalars().all()

    if not credentials:
        return 0

    count = 0
    for cred in credentials:
        try:
            # Encrypt access_token if present
            if cred.access_token:
                cred.set_access_token(cred.access_token)
                logger.info(f"[{schema}] Encrypted eBay access_token for ID {cred.id}")

            # Encrypt refresh_token if present
            if cred.refresh_token:
                cred.set_refresh_token(cred.refresh_token)
                logger.info(f"[{schema}] Encrypted eBay refresh_token for ID {cred.id}")

            count += 1

        except Exception as e:
            logger.error(f"[{schema}] Failed to encrypt tokens for eBay credential {cred.id}: {e}")
            continue

    db.commit()
    return count


def migrate_etsy_tokens(db, schema: str):
    """Migrate Etsy tokens for a specific schema."""
    # Use schema_translate_map for ORM queries (survives commit/rollback)
    db = db.execution_options(schema_translate_map={"tenant": schema})

    # Get credentials with plaintext tokens
    credentials = db.execute(
        select(EtsyCredentials).where(
            EtsyCredentials.access_token.isnot(None),
            EtsyCredentials.access_token_encrypted.is_(None)
        )
    ).scalars().all()

    if not credentials:
        return 0

    count = 0
    for cred in credentials:
        try:
            # Encrypt access_token if present
            if cred.access_token:
                cred.set_access_token(cred.access_token)
                logger.info(f"[{schema}] Encrypted Etsy access_token for ID {cred.id}")

            # Encrypt refresh_token if present
            if cred.refresh_token:
                cred.set_refresh_token(cred.refresh_token)
                logger.info(f"[{schema}] Encrypted Etsy refresh_token for ID {cred.id}")

            count += 1

        except Exception as e:
            logger.error(f"[{schema}] Failed to encrypt tokens for Etsy credential {cred.id}: {e}")
            continue

    db.commit()
    return count


def main():
    """Main migration function."""
    logger.info("=" * 80)
    logger.info("Starting OAuth tokens encryption migration (Phase 1.1)")
    logger.info("=" * 80)

    # Check encryption is configured
    encryption_service = get_encryption_service()
    if not encryption_service.is_configured:
        logger.error("❌ Encryption not configured. Set ENCRYPTION_KEY in .env")
        logger.error("   Generate a key with: python -c \"from shared.encryption import generate_encryption_key; print(generate_encryption_key())\"")
        return 1

    logger.info("✅ Encryption service configured")

    with get_db_context() as db:
        # Get all user schemas
        user_schemas = get_user_schemas(db)
        logger.info(f"Found {len(user_schemas)} user schemas")

        total_ebay = 0
        total_etsy = 0

        for schema in user_schemas:
            logger.info(f"\nProcessing schema: {schema}")

            # Migrate eBay tokens
            ebay_count = migrate_ebay_tokens(db, schema)
            total_ebay += ebay_count
            if ebay_count > 0:
                logger.info(f"  ✓ Migrated {ebay_count} eBay credentials")

            # Migrate Etsy tokens
            etsy_count = migrate_etsy_tokens(db, schema)
            total_etsy += etsy_count
            if etsy_count > 0:
                logger.info(f"  ✓ Migrated {etsy_count} Etsy credentials")

        logger.info("\n" + "=" * 80)
        logger.info("Migration completed!")
        logger.info(f"  eBay: {total_ebay} credentials encrypted")
        logger.info(f"  Etsy: {total_etsy} credentials encrypted")
        logger.info("=" * 80)

        return 0


if __name__ == "__main__":
    exit(main())
