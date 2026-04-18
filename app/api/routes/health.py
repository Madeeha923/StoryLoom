from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse, summary="Health check endpoint")
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="api")

