"""
eBay API Routes

Exports routers for eBay integration.
"""

from api.ebay.cancellations import router as cancellations_router
from api.ebay.dashboard import router as dashboard_router
from api.ebay.inquiries import router as inquiries_router
from api.ebay.main import router
from api.ebay.payment_disputes import router as payment_disputes_router
from api.ebay.products import router as products_router
from api.ebay.refunds import router as refunds_router
from api.ebay.returns import router as returns_router

__all__ = [
    "router",
    "products_router",
    "returns_router",
    "cancellations_router",
    "refunds_router",
    "payment_disputes_router",
    "inquiries_router",
    "dashboard_router",
]
