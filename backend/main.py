"""
Stoflow Backend - Application FastAPI

Point d'entree principal de l'application FastAPI.
"""

from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.auth import router as auth_router
from api.attributes import router as attributes_router
from api.ebay import router as ebay_router, products_router as ebay_products_router
from api.ebay_oauth import router as ebay_oauth_router
from api.ebay_webhook import router as ebay_webhook_router
from api.etsy import router as etsy_router
from api.etsy_oauth import router as etsy_oauth_router
from api.integrations import router as integrations_router
from api.plugin import router as plugin_router
from api.products import router as products_router
from api.stripe_routes import router as stripe_router
from api.subscription import router as subscription_router
from api.vinted import router as vinted_router  # Now from api/vinted/__init__.py
from middleware.rate_limit import rate_limit_middleware
from middleware.security_headers import SecurityHeadersMiddleware
from models.user.plugin_task import PluginTask, TaskStatus
from services.file_service import FileService
from services.datadome_scheduler import (
    start_datadome_scheduler,
    stop_datadome_scheduler,
    get_datadome_scheduler
)
from shared.config import settings
from shared.database import SessionLocal
from shared.logging_setup import setup_logging

# Configuration du logging
logger = setup_logging()

# Creation de l'application FastAPI
app = FastAPI(
    title=settings.app_name,
    description="API Backend pour Stoflow - Plateforme SaaS de gestion d'annonces multi-plateformes",
    version="1.0.0",
    debug=settings.debug,
)


def cleanup_all_pending_plugin_tasks() -> dict[str, int]:
    """
    Annule TOUTES les tâches plugin PENDING/PROCESSING au démarrage.

    CRITICAL (2025-12-18): Évite le flood Vinted au restart.
    - Annule TOUTES les tâches PENDING (pas seulement les vieilles)
    - Annule TOUTES les tâches PROCESSING (plugin crashé)
    - Empêche le plugin de récupérer des tâches abandonnées

    Returns:
        dict: {"cancelled": int, "schemas_processed": int}
    """
    db = SessionLocal()
    cancelled_total = 0
    schemas_processed = 0

    try:
        # Récupérer tous les schémas utilisateur
        result = db.execute(text(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name LIKE 'user_%'"
        ))
        user_schemas = [row[0] for row in result]

        for schema in user_schemas:
            try:
                # Skip invalid schemas (template, test schemas without tables)
                if schema in ("user_invalid", "template_tenant"):
                    continue

                # Vérifier que la table plugin_tasks existe dans ce schéma
                table_exists = db.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = :schema AND table_name = 'plugin_tasks'
                    )
                """), {"schema": schema}).scalar()

                if not table_exists:
                    continue

                # Configurer le search_path pour ce schéma
                db.execute(text(f"SET LOCAL search_path TO {schema}, public"))

                # Annuler TOUTES les tâches PENDING
                pending_result = db.execute(text("""
                    UPDATE plugin_tasks
                    SET status = :cancelled_status,
                        error_message = :error_msg,
                        completed_at = NOW()
                    WHERE status = :pending_status
                """), {
                    "cancelled_status": TaskStatus.CANCELLED.value,
                    "pending_status": TaskStatus.PENDING.value,
                    "error_msg": "Auto-cancelled at backend startup",
                })
                pending_cancelled = pending_result.rowcount

                # Annuler TOUTES les tâches PROCESSING (plugin crashé)
                processing_result = db.execute(text("""
                    UPDATE plugin_tasks
                    SET status = :cancelled_status,
                        error_message = :error_msg,
                        completed_at = NOW()
                    WHERE status = :processing_status
                """), {
                    "cancelled_status": TaskStatus.CANCELLED.value,
                    "processing_status": TaskStatus.PROCESSING.value,
                    "error_msg": "Auto-cancelled at backend startup (stale processing)",
                })
                processing_cancelled = processing_result.rowcount

                schema_total = pending_cancelled + processing_cancelled
                if schema_total > 0:
                    logger.info(
                        f"🧹 {schema}: {schema_total} tâches annulées "
                        f"({pending_cancelled} pending, {processing_cancelled} processing)"
                    )
                    cancelled_total += schema_total

                schemas_processed += 1

            except Exception as e:
                logger.warning(f"Erreur nettoyage {schema}: {e}")
                db.rollback()  # CRITICAL: Rollback to recover from failed transaction
                continue

        db.commit()

    except Exception as e:
        logger.error(f"Erreur nettoyage global des tâches: {e}")
        db.rollback()
    finally:
        db.close()

    return {"cancelled": cancelled_total, "schemas_processed": schemas_processed}


# Startup event: créer répertoire uploads
@app.on_event("startup")
async def startup_event():
    """
    Initialisation au démarrage de l'application.

    Security (2025-12-05):
    - Valide que les secrets requis sont configurés via .env

    Safety (2025-12-18):
    - Nettoie les tâches plugin obsolètes pour éviter flood Vinted
    """
    # ===== SECURITY FIX (2025-12-05): Validate secrets at startup =====
    required_secrets = [
        "jwt_secret_key",
        "database_url",
        "openai_api_key",
    ]

    missing_secrets = []
    for secret in required_secrets:
        value = getattr(settings, secret, None)
        if not value or value == "":
            missing_secrets.append(secret)

    if missing_secrets:
        error_msg = (
            f"Missing required secrets in .env file:\n" +
            "\n".join(f"  - {secret.upper()}" for secret in missing_secrets) +
            "\n\nPlease configure these in your .env file (see .env.example)"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # ===== SAFETY FIX (2025-12-18): Cleanup ALL pending plugin tasks =====
    # CRITIQUE: Évite le flood Vinted au redémarrage
    # Annule TOUTES les tâches PENDING/PROCESSING (pas seulement les vieilles)
    # car elles appartiennent à une session précédente et ne doivent pas être exécutées
    cleanup_result = cleanup_all_pending_plugin_tasks()
    if cleanup_result["cancelled"] > 0:
        logger.warning(
            f"🧹 Nettoyage tâches au démarrage: {cleanup_result['cancelled']} annulées "
            f"dans {cleanup_result['schemas_processed']} schémas"
        )
    else:
        logger.info("✅ Aucune tâche en attente à nettoyer")

    # Créer répertoire uploads
    FileService.ensure_upload_directory()
    logger.info("Upload directory initialized")
    logger.info("✅ All required secrets configured")

    # ===== DATADOME SCHEDULER (2025-12-19) =====
    # DISABLED: En stand-by - sera réactivé avec logique basée sur compteur de requêtes
    # TODO: Réactiver quand la logique de ping par nombre de requêtes sera implémentée
    # try:
    #     start_datadome_scheduler()
    #     logger.info("🛡️ DataDome scheduler started")
    # except Exception as e:
    #     logger.error(f"Failed to start DataDome scheduler: {e}")
    logger.info("🛡️ DataDome scheduler DISABLED (stand-by)")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on application shutdown.
    """
    # Stop DataDome scheduler (DISABLED - stand-by)
    # try:
    #     scheduler = get_datadome_scheduler()
    #     if scheduler:
    #         stop_datadome_scheduler(scheduler)
    #         logger.info("🛡️ DataDome scheduler stopped")
    # except Exception as e:
    #     logger.error(f"Error stopping DataDome scheduler: {e}")
    pass

# ===== SECURITY MIDDLEWARE (2025-12-05) =====

# Security Headers (HSTS, X-Frame-Options, CSP, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# CORS Configuration (Updated: 2025-12-18 - Sécurisé en production)
# - DEV: Autorise tout (plugin, frontend, swagger) pour faciliter le développement
# - PROD: Restreint aux origines configurées dans CORS_ORIGINS
if settings.is_production:
    # Production: utiliser les origines configurées
    cors_origins = settings.get_cors_origins_list()
    if not cors_origins or cors_origins == [""]:
        logger.warning(
            "⚠️ CORS_ORIGINS non configuré en production! "
            "Configurez CORS_ORIGINS dans .env (ex: https://app.stoflow.fr,https://stoflow.fr)"
        )
        cors_origins = []  # Bloque tout si non configuré

    logger.info(f"🔒 CORS Production: origines autorisées = {cors_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,  # OK avec origines explicites
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Dev-User-Id"],
        expose_headers=["X-Total-Count"],
    )
else:
    # Développement: autorise tout pour faciliter les tests
    logger.info("🔓 CORS Développement: toutes les origines autorisées")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # credentials=False requis avec origins=*
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

# Rate Limiting (protection bruteforce)
app.middleware("http")(rate_limit_middleware)

# Enregistrement des routes
app.include_router(auth_router, prefix="/api")
app.include_router(attributes_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(integrations_router, prefix="/api")
app.include_router(plugin_router, prefix="/api")
app.include_router(stripe_router, prefix="/api")
app.include_router(subscription_router, prefix="/api")
app.include_router(vinted_router, prefix="/api")
app.include_router(ebay_router, prefix="/api")
app.include_router(ebay_products_router, prefix="/api")
app.include_router(ebay_oauth_router, prefix="/api")
app.include_router(ebay_webhook_router, prefix="/api")
app.include_router(etsy_router, prefix="/api")
app.include_router(etsy_oauth_router, prefix="/api")

# Monter le répertoire uploads pour servir les images statiques
# IMPORTANT: Ceci doit être fait APRÈS l'inclusion de tous les routers
# pour éviter les conflits de routes
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/", tags=["Health"])
def root():
    """
    Route de sante / bienvenue.

    Returns:
        Message de bienvenue
    """
    return {
        "message": f"Bienvenue sur {settings.app_name} API",
        "version": "1.0.0",
        "environment": settings.app_env,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Verification de sante de l'API.

    Returns:
        Statut de sante
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.app_env,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
