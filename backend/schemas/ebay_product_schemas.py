"""
eBay Product Schemas

Pydantic schemas for eBay product API endpoints.

Created: 2026-01-20
Author: Claude
"""

import json
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EbayProductResponse(BaseModel):
    """Response schema for eBay product."""

    id: int
    ebay_sku: str
    product_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: str = "EUR"
    brand: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    condition: Optional[str] = None
    quantity: int = 1
    marketplace_id: str = "EBAY_FR"
    ebay_listing_id: Optional[int] = None
    status: str = "active"
    image_urls: Optional[list[str]] = None
    image_url: Optional[str] = None  # First image for preview
    ebay_listing_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_parsed_images(cls, obj):
        """Create response with parsed image_urls JSON."""
        data = {
            "id": obj.id,
            "ebay_sku": obj.ebay_sku,
            "product_id": obj.product_id,
            "title": obj.title,
            "description": obj.description,
            "price": obj.price,
            "currency": obj.currency or "EUR",
            "brand": obj.brand,
            "size": obj.size,
            "color": obj.color,
            "condition": obj.condition,
            "quantity": obj.quantity or 1,
            "marketplace_id": obj.marketplace_id or "EBAY_FR",
            "ebay_listing_id": obj.ebay_listing_id,
            "status": obj.status or "active",
            "image_urls": None,
            "image_url": None,
            "ebay_listing_url": None,
        }
        # Parse image_urls from JSON string
        if obj.image_urls:
            try:
                parsed_urls = json.loads(obj.image_urls)
                data["image_urls"] = parsed_urls
                # Set first image as preview
                if parsed_urls and len(parsed_urls) > 0:
                    data["image_url"] = parsed_urls[0]
            except (json.JSONDecodeError, TypeError):
                data["image_urls"] = None
        # Build eBay listing URL if listing_id exists
        if obj.ebay_listing_id:
            data["ebay_listing_url"] = f"https://www.ebay.fr/itm/{obj.ebay_listing_id}"
        return cls(**data)


class EbayProductListResponse(BaseModel):
    """Response schema for eBay products list."""

    items: list[EbayProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    # Global stats (not affected by pagination)
    active_count: int = 0
    inactive_count: int = 0
    out_of_stock_count: int = 0


class ImportRequest(BaseModel):
    """Request schema for import."""

    marketplace_id: str = "EBAY_FR"


class ImportResponse(BaseModel):
    """Response schema for import."""

    imported: int
    updated: int
    skipped: int
    errors: int
    details: list[dict]


class EnrichRequest(BaseModel):
    """Request schema for enrichment."""

    batch_size: int = 100
    only_without_price: bool = True


class EnrichResponse(BaseModel):
    """Response schema for enrichment."""

    enriched: int
    errors: int
    remaining: int
    details: list[dict]


class RefreshAspectsResponse(BaseModel):
    """Response schema for aspects refresh."""

    updated: int
    errors: int
    remaining: int


class LinkProductRequest(BaseModel):
    """
    Request body for linking EbayProduct to Product.

    - If product_id is provided: link to existing Product
    - If product_id is None: create new Product from EbayProduct data
    """

    product_id: Optional[int] = None  # None = create new Product

    # Optional overrides when creating new Product (ignored if product_id is set)
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    brand: Optional[str] = None


class EbayLinkResponse(BaseModel):
    """Response for link operation."""

    success: bool
    ebay_product_id: int
    product_id: int
    created: bool
    images_copied: Optional[int] = None
    product: Optional[dict] = None


class EbayUnlinkResponse(BaseModel):
    """Response for unlink operation."""

    success: bool
    ebay_product_id: int
