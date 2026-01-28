"""
Vinted Orders Routes

Endpoints pour la gestion des commandes Vinted:
- GET /orders: Liste des commandes
- POST /orders/sync: Synchroniser les commandes

Methods:
- Sans year/month: sync via /my_orders (ALL completed orders)
- Avec year+month: sync via /wallet/invoices (wallet transactions only)

/my_orders est la méthode par défaut car /wallet/invoices ne capture
pas les paiements par carte directe.

Updated: 2025-12-19 - Intégration système de jobs
Updated: 2026-01-05 - Fusion sync/sync-month, suppression labels et deletions
Updated: 2026-01-13 - sync_orders() par défaut, sync_orders_by_month optionnel

Author: Claude
Date: 2025-12-17
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_user_db
from api.workflows import WorkflowStartResponse
from models.vinted.vinted_order import VintedOrder
from shared.logging import get_logger
from .shared import get_active_vinted_connection

logger = get_logger(__name__)

router = APIRouter()


@router.get("/orders")
async def list_orders(
    user_db: tuple = Depends(get_user_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """
    Liste les commandes Vinted en BDD.

    Returns:
        {"orders": list, "total": int}
    """
    db, current_user = user_db

    try:
        total = db.query(VintedOrder).count()
        orders = db.query(VintedOrder).order_by(
            VintedOrder.transaction_id.desc()
        ).offset(offset).limit(limit).all()

        orders_data = []
        for order in orders:
            orders_data.append({
                "transaction_id": order.transaction_id,
                "buyer_id": order.buyer_id,
                "buyer_login": order.buyer_login,
                "status": order.status,
                "total_price": float(order.total_price) if order.total_price else None,
                "currency": order.currency,
                "shipping_price": float(order.shipping_price) if order.shipping_price else None,
                "service_fee": float(order.service_fee) if order.service_fee else None,
                "seller_revenue": float(order.seller_revenue) if order.seller_revenue else None,
                "carrier": order.carrier,
                "tracking_number": order.tracking_number,
                "created_at_vinted": order.created_at_vinted.isoformat() if order.created_at_vinted else None,
                "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
                "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
                "completed_at": order.completed_at.isoformat() if order.completed_at else None,
                "products": [
                    {
                        "id": p.id,
                        "vinted_item_id": p.vinted_item_id,
                        "product_id": p.product_id,
                        "title": p.title,
                        "price": float(p.price) if p.price else None,
                        "size": p.size,
                        "brand": p.brand,
                        "photo_url": p.photo_url
                    }
                    for p in order.products
                ]
            })

        return {"orders": orders_data, "total": total, "limit": limit, "offset": offset}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur liste commandes: {str(e)}"
        )


@router.post("/orders/sync", response_model=WorkflowStartResponse)
async def sync_orders(
    user_db: tuple = Depends(get_user_db),
    year: Optional[int] = Query(None, ge=2020, le=2100, description="Year (optional)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Month 1-12 (optional)"),
):
    """
    Sync orders from Vinted via Temporal workflow.

    - Without year/month: sync via /my_orders (ALL completed orders)
    - With year+month: sync via /wallet/invoices (wallet transactions only)

    Starts VintedOrdersSyncWorkflow and returns immediately.

    Args:
        year: Year (optional, if provided with month: uses /wallet/invoices)
        month: Month 1-12 (optional, if provided with year: uses /wallet/invoices)

    Returns:
        WorkflowStartResponse with workflow_id
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config
    from temporal.workflows.vinted.orders_sync_workflow import VintedOrdersSyncParams, VintedOrdersSyncWorkflow

    config = get_temporal_config()
    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled",
        )

    db, current_user = user_db
    connection = get_active_vinted_connection(db, current_user.id)

    workflow_id = f"vinted-orders-sync-user-{current_user.id}"
    params = VintedOrdersSyncParams(
        user_id=current_user.id,
        shop_id=connection.vinted_user_id,
        year=year or 0,
        month=month or 0,
    )

    client = await get_temporal_client()
    await client.start_workflow(
        VintedOrdersSyncWorkflow.run,
        params,
        id=workflow_id,
        task_queue=config.temporal_vinted_task_queue,
    )

    logger.info(f"Started workflow: {workflow_id}")
    return WorkflowStartResponse(workflow_id=workflow_id, status="started")


