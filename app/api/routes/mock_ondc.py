from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/mock/ondc", tags=["Mock ONDC"])


@router.post(
    "/catalog/upload",
    summary="Simulate uploading the generated catalog payload to an ONDC-style endpoint",
)
async def mock_ondc_catalog_upload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    product = payload.get("product", {}) if isinstance(payload, dict) else {}
    product_title = str(product.get("title", "")).strip()
    product_name = str(product.get("name", "")).strip()

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload payload is required.",
        )

    if not product_title and not product_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload payload must include a product title or product name.",
        )

    submission_reference = f"ondc-mock-{uuid4().hex[:12]}"
    submitted_at = datetime.now(timezone.utc).isoformat()

    return {
        "provider": "mock-ondc",
        "status": "accepted",
        "message": (
            "StoryLoom triggered the Registrar handoff and submitted the listing to the mock ONDC endpoint. "
            "No real ONDC marketplace API was called."
        ),
        "submission_reference": submission_reference,
        "submitted_at": submitted_at,
        "listing_preview": {
            "product_name": product_name or product_title,
            "product_title": product_title or product_name,
            "sku_slug": payload.get("sku_slug"),
        },
        "submitted_payload": payload,
    }
