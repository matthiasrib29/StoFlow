"""
Vinted Dependencies

Helpers and factories for Vinted routes.
"""

from datetime import datetime
from typing import Any, Optional, Tuple

from sqlalchemy.orm import Session

from models.public.user import User
from models.user.vinted_connection import VintedConnection
from models.user.marketplace_job import MarketplaceJob
from models.user.product import Product
from services.marketplace.marketplace_job_processor import MarketplaceJobProcessor
from services.marketplace.marketplace_job_service import MarketplaceJobService
from services.vinted import VintedJobService


def build_job_response_dict(
    job: MarketplaceJob,
    db: Session,
    service: Optional[Any] = None,
    include_progress: bool = True,
    batch_id_override: Optional[str] = None,
) -> dict:
    """
    Build a JobResponse dict with all fields.

    Args:
        job: MarketplaceJob instance
        db: Database session
        service: VintedJobService or MarketplaceJobService (optional)
        include_progress: Whether to fetch progress (default True)
        batch_id_override: Override batch_id (for newly created batch jobs)

    Returns:
        Dict ready for JobResponse schema
    """
    # Use provided service or create MarketplaceJobService
    if service is None:
        service = MarketplaceJobService(db)

    # Get action type
    action_type = service.get_action_type_by_id(job.action_type_id)

    # Get progress if requested and service supports it
    progress = None
    if include_progress and hasattr(service, 'get_job_progress'):
        progress = service.get_job_progress(job.id)

    # Get product title if job has a product_id
    product_title = None
    if job.product_id:
        product = db.query(Product).filter(Product.id == job.product_id).first()
        if product:
            product_title = product.title

    # Determine batch_id
    batch_id = batch_id_override
    if batch_id is None and job.batch_job:
        batch_id = job.batch_job.batch_id

    return {
        "id": job.id,
        "batch_id": batch_id,
        "action_type_id": job.action_type_id,
        "action_code": action_type.code if action_type else None,
        "action_name": action_type.name if action_type else None,
        "product_id": job.product_id,
        "product_title": product_title,
        "status": job.status.value,
        "priority": job.priority,
        "error_message": job.error_message,
        "retry_count": job.retry_count,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "expires_at": job.expires_at,
        "created_at": job.created_at,
        "progress": progress if progress and progress.get("current") is not None else None,
    }


async def create_and_execute_vinted_job(
    db: Session,
    user_id: int,
    shop_id: int,
    action_code: str,
    product_id: Optional[int] = None,
    process_now: bool = True,
) -> dict:
    """
    Create a Vinted job and optionally execute it.

    Args:
        db: Database session
        user_id: User ID
        shop_id: Vinted shop ID (vinted_user_id)
        action_code: Job action code (sync, update, publish, delete)
        product_id: Product ID (None for sync operations)
        process_now: Execute immediately if True

    Returns:
        Dict with job_id, status, and optional result
    """
    job_service = VintedJobService(db)

    # Create job
    job = job_service.create_job(
        action_code=action_code,
        product_id=product_id
    )

    # Store values BEFORE commit (SET LOCAL search_path resets on commit)
    job_id = job.id
    job_status = job.status.value

    db.commit()
    db.refresh(job)

    response = {
        "job_id": job_id,
        "status": job_status,
    }

    if product_id:
        response["product_id"] = product_id

    # Execute immediately if requested
    if process_now:
        processor = MarketplaceJobProcessor(
            db, user_id=user_id, shop_id=shop_id, marketplace="vinted"
        )
        result = await processor._execute_job(job)
        response["result"] = result
        response["status"] = "completed" if result.get("success") else "failed"

    return response
