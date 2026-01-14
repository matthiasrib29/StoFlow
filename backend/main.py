"""
Stoflow Backend - Application FastAPI

Point d'entree principal de l'application FastAPI.
"""

from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.admin import router as admin_router
from api.admin_attributes import router as admin_attributes_router
from api.admin_audit import router as admin_audit_router
from api.admin_docs import router as admin_docs_router
from api.admin_stats import router as admin_stats_router
from api.auth import router as auth_router
from api.attributes import router as attributes_router
from api.batches import router as batches_router
from api.docs import router as docs_router
# eBay routers (re-enabled 2026-01-03)
from api.ebay import router as ebay_router, products_router as ebay_products_router, returns_router as ebay_returns_router, cancellations_router as ebay_cancellations_router, refunds_router as ebay_refunds_router, payment_disputes_router as ebay_payment_disputes_router, inquiries_router as ebay_inquiries_router, dashboard_router as ebay_dashboard_router
from api.ebay_oauth import router as ebay_oauth_router
from api.ebay_webhook import router as ebay_webhook_router
# TEMPORARILY DISABLED - Etsy uses PlatformMapping model (not yet implemented)
# from api.etsy import router as etsy_router
# from api.etsy_oauth import router as etsy_oauth_router
# REMOVED (2026-01-09): Plugin now communicates via WebSocket (no HTTP endpoints needed)
# from api.plugin import router as plugin_router
from api.pricing import router as pricing_router
from api.products import router as products_router
from api.text_generator import router as text_generator_router
from api.user_settings import router as user_settings_router
from api.stripe_routes import router as stripe_router
from api.subscription import router as subscription_router
from api.vinted import router as vinted_router  # Now from api/vinted/__init__.py
from middleware.error_handler import (
    stoflow_error_handler,
    validation_error_handler,
    http_exception_handler,
    generic_exception_handler,
)
from middleware.rate_limit import rate_limit_middleware
from middleware.security_headers import SecurityHeadersMiddleware
from services.r2_service import r2_service
from services.datadome_scheduler import (
    start_datadome_scheduler,
    stop_datadome_scheduler,
    get_datadome_scheduler
)
from services.websocket_service import sio
from shared.config import settings
from shared.exceptions import StoflowError
# Note: SessionLocal removed - no longer needed after plugin tasks cleanup removal
from shared.logging_setup import setup_logging

# Configuration du logging
logger = setup_logging()


# =============================================================================
# LIFESPAN CONTEXT MANAGER (replaces @app.on_event)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Startup: Validates configuration and initializes services.
    Shutdown: Performs cleanup (currently minimal).
    """
    # ===== STARTUP =====
    logger.info("🚀 Starting StoFlow backend...")

    # SECURITY FIX (2025-12-05): Validate secrets at startup
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

    logger.info("✅ All required secrets configured")

    # ===== R2 STORAGE (2025-12-23) =====
    # R2 is REQUIRED for image storage (no local fallback)
    if r2_service.is_available:
        logger.info(f"☁️ Cloudflare R2 storage enabled (bucket: {settings.r2_bucket_name})")
    else:
        error_msg = (
            "R2 storage not configured. Image uploads will fail.\n"
            "Set these environment variables:\n"
            "  - R2_ACCESS_KEY_ID\n"
            "  - R2_SECRET_ACCESS_KEY\n"
            "  - R2_ENDPOINT\n"
            "  - R2_PUBLIC_URL (optional but recommended)"
        )
        if settings.is_production:
            logger.error(error_msg)
            raise ValueError("R2 storage is required in production")
        else:
            logger.warning(f"⚠️ {error_msg}")

    # ===== DATADOME SCHEDULER (2025-12-19) =====
    # DISABLED: En stand-by - sera réactivé avec logique basée sur compteur de requêtes
    # TODO: Réactiver quand la logique de ping par nombre de requêtes sera implémentée
    logger.info("🛡️ DataDome scheduler DISABLED (stand-by)")

    yield  # Application runs here

    # ===== SHUTDOWN =====
    logger.info("🛑 Shutting down StoFlow backend...")
    # Note: DataDome scheduler shutdown is currently disabled (stand-by mode)


# Creation de l'application FastAPI
app = FastAPI(
    title=settings.app_name,
    description="API Backend pour Stoflow - Plateforme SaaS de gestion d'annonces multi-plateformes",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# ===== WEBSOCKET INTEGRATION (2026-01-08) =====
# Wrap FastAPI app with SocketIO for real-time plugin communication
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path="/socket.io",
)
logger.info("🔌 WebSocket server enabled at /socket.io")


# ===== EXCEPTION HANDLERS (2026-01-08) =====
# Global error sanitization to prevent information disclosure (OWASP A05:2021)
# Order matters: more specific handlers first, generic handler last
app.add_exception_handler(StoflowError, stoflow_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ===== SECURITY MIDDLEWARE (2025-12-05) =====

# Proxy Headers Middleware (2025-12-23)
# Fix for Railway/reverse proxy: ensures correct protocol in redirects
# Without this, FastAPI's redirect_slashes uses HTTP instead of HTTPS
class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to trust X-Forwarded-Proto header from reverse proxy."""

    async def dispatch(self, request: Request, call_next):
        # Get the original protocol from proxy headers
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto:
            # Update the scope to reflect the original protocol
            request.scope["scheme"] = forwarded_proto
        return await call_next(request)

app.add_middleware(ProxyHeadersMiddleware)

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
    # Regex pour autoriser les extensions de navigateur (Chrome/Firefox)
    # Les extensions ont des origines comme chrome-extension://... ou moz-extension://...
    extension_origin_regex = r"^(chrome-extension|moz-extension)://.*$"
    logger.info(f"🔌 CORS Production: extensions autorisées via regex = {extension_origin_regex}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=extension_origin_regex,
        allow_credentials=True,  # OK avec origines explicites
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
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
app.include_router(admin_router, prefix="/api")
app.include_router(admin_attributes_router, prefix="/api")
app.include_router(admin_audit_router, prefix="/api")
app.include_router(admin_stats_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(batches_router, prefix="/api")  # Generic batch jobs (multi-marketplace)
app.include_router(docs_router, prefix="/api")  # Public documentation (no auth required)
app.include_router(admin_docs_router, prefix="/api")  # Admin documentation CRUD (admin only)
app.include_router(attributes_router, prefix="/api")
app.include_router(pricing_router, prefix="/api")  # Pricing algorithm endpoint
app.include_router(products_router, prefix="/api")
app.include_router(text_generator_router, prefix="/api")  # Text generation endpoint
app.include_router(user_settings_router, prefix="/api")  # User settings endpoint
# REMOVED (2026-01-09): Plugin communication via WebSocket only
# app.include_router(plugin_router, prefix="/api")
app.include_router(stripe_router, prefix="/api")
app.include_router(subscription_router, prefix="/api")
app.include_router(vinted_router, prefix="/api")
# eBay routers (re-enabled 2026-01-03)
app.include_router(ebay_router, prefix="/api")
app.include_router(ebay_products_router, prefix="/api")
app.include_router(ebay_returns_router, prefix="/api")
app.include_router(ebay_cancellations_router, prefix="/api")
app.include_router(ebay_refunds_router, prefix="/api")
app.include_router(ebay_payment_disputes_router, prefix="/api")
app.include_router(ebay_inquiries_router, prefix="/api")
app.include_router(ebay_dashboard_router, prefix="/api")
app.include_router(ebay_oauth_router, prefix="/api")
app.include_router(ebay_webhook_router, prefix="/api")
# TEMPORARILY DISABLED - Etsy uses PlatformMapping model (not yet implemented)
# app.include_router(etsy_router, prefix="/api")
# app.include_router(etsy_oauth_router, prefix="/api")

# NOTE (2025-12-23): Images are served via Cloudflare R2 CDN
# No local StaticFiles mount needed


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
        "storage": {
            "type": "r2" if r2_service.is_available else "local",
            "bucket": settings.r2_bucket_name if r2_service.is_available else None,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:socket_app",  # Use socket_app instead of app for WebSocket support
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
