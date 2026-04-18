from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.schemas.product_intake import ProductIntakeResponse
from app.services.product_intake_service import (
    ProductIntakeService,
    get_product_intake_service,
)

router = APIRouter()


@router.post(
    "/process",
    response_model=ProductIntakeResponse,
    summary="Process image, optional text, and optional audio into cleaned product copy",
)
async def process_product_intake(
    image: UploadFile = File(...),
    text: str | None = Form(default=None),
    audio: UploadFile | None = File(default=None),
    intake_service: ProductIntakeService = Depends(get_product_intake_service),
) -> ProductIntakeResponse:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The `image` file must be a valid image upload.",
        )

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image is empty.",
        )

    audio_bytes: bytes | None = None
    audio_filename: str | None = None
    audio_content_type: str | None = None
    if audio is not None:
        audio_bytes = await audio.read()
        audio_filename = audio.filename or "audio-input"
        audio_content_type = audio.content_type
        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded audio file is empty.",
            )

    try:
        return await intake_service.process_uploads(
            image_bytes=image_bytes,
            image_filename=image.filename or "image-upload",
            image_content_type=image.content_type,
            text_input=text,
            audio_bytes=audio_bytes,
            audio_filename=audio_filename,
            audio_content_type=audio_content_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI processing failed: {exc}",
        ) from exc

