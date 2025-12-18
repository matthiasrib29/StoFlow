"""
Configuration Vinted Headers

Configuration centralisée des headers Vinted basée sur reverse engineering.
Les headers sont générés dynamiquement selon l'action/endpoint.

Business Rules (2025-12-11):
- Headers de base envoyés pour TOUTES les requêtes
- Headers conditionnels ajoutés selon l'action (upload, transaction, etc.)
- csrf_token et anon_id sont injectés depuis vinted_credentials (unique par user)
- Pas de User-Agent, Cookie, Sec-Fetch-* (gérés automatiquement par Firefox)

Author: Claude
Date: 2025-12-11
"""

# ============================================================================
# HEADERS DE BASE (toujours envoyés)
# ============================================================================

VINTED_HEADERS_BASE = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr",
    "Content-Type": "application/json",
    "Priority": "u=3",
}

# ============================================================================
# HEADERS CONDITIONNELS PAR ACTION
# ============================================================================

VINTED_HEADERS_CONDITIONAL = {
    # Upload / Edit articles
    "upload_item": {
        "X-Upload-Form": "true",
        "X-Enable-Multiple-Size-Groups": "true",
    },
    "edit_item": {
        "X-Upload-Form": "true",
        "X-Enable-Multiple-Size-Groups": "true",
    },
    "edit_draft": {
        "X-Upload-Form": "true",
        "X-Enable-Multiple-Size-Groups": "true",
    },
    "delete_item": {
        "X-Upload-Form": "true",
    },

    # Transactions / Orders
    "transactions": {
        "X-Money-Object": "true",
    },
    "orders": {
        "X-Money-Object": "true",
    },

    # Auth
    "auth": {
        "X-Browser-Compat": "2",
    },

    # Brand
    "brand": {
        "Mda-Brand": "true",
    },
}

# ============================================================================
# PATTERNS D'URL POUR DÉTECTION AUTOMATIQUE
# ============================================================================

VINTED_URL_PATTERNS = {
    "upload_item": ["/item_upload", "/items", "/photos"],
    "edit_item": ["/items/", "/edit"],
    "edit_draft": ["/draft"],
    "delete_item": ["/items/", "/delete"],
    "transactions": ["/transactions"],
    "orders": ["/orders", "/help_center/recent"],
    "auth": ["/web/api/auth", "/auth/refresh"],
    "brand": ["/brand"],
}

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "VINTED_HEADERS_BASE",
    "VINTED_HEADERS_CONDITIONAL",
    "VINTED_URL_PATTERNS",
]
