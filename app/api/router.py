from fastapi import APIRouter

from app.api.routes.generate_listing import router as generate_listing_router
from app.api.routes.health import router as health_router
from app.api.routes.mock_ondc import router as mock_ondc_router
from app.api.routes.product_intake import router as product_intake_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(generate_listing_router, tags=["Listing Generation"])
api_router.include_router(mock_ondc_router)
api_router.include_router(
    product_intake_router,
    prefix="/product-intake",
    tags=["Product Intake"],
)
