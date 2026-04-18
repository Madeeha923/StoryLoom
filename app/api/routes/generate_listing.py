from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.pipeline.automation import EcommerceAutomationPipeline
from app.schemas.generate_listing import GenerateListingResponse
from app.schemas.product_intake import ProductIntakeResponse
from app.services.product_intake_service import (
    ProductIntakeService,
    get_product_intake_service,
)

router = APIRouter()


def get_listing_pipeline() -> EcommerceAutomationPipeline:
    return EcommerceAutomationPipeline()


@router.post(
    "/generate-listing",
    response_model=GenerateListingResponse,
    summary="Accept image and optional text/audio, run the full listing pipeline, and return the final package",
)
async def generate_listing(
    image: UploadFile = File(...),
    text: str | None = Form(default=None),
    audio: UploadFile | None = File(default=None),
    simulated_confirmation_response: str = Form(default="approved"),
    intake_service: ProductIntakeService = Depends(get_product_intake_service),
    pipeline: EcommerceAutomationPipeline = Depends(get_listing_pipeline),
) -> GenerateListingResponse:
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
        intake_result = await intake_service.process_uploads(
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
            detail=f"OpenAI intake processing failed: {exc}",
        ) from exc

    pipeline_payload = _build_pipeline_payload(
        intake_result=intake_result,
        image_bytes=image_bytes,
        image_content_type=image.content_type,
        image_filename=image.filename or "image-upload",
        original_text=text,
        simulated_confirmation_response=simulated_confirmation_response,
    )

    try:
        pipeline_result = await pipeline.execute(pipeline_payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Pipeline execution failed: {exc}",
        ) from exc

    copywriter_output = pipeline_result.get("stages", {}).get("copywriter", {}).get("output", {})
    studio_output = pipeline_result.get("stages", {}).get("studio", {}).get("output", {})
    image_output = pipeline_result.get("stages", {}).get("image_generator", {}).get("output", {})
    image_status = str(
        pipeline_result.get("stages", {}).get("image_generator", {}).get("status", "")
    ).strip()
    generated_images = _coerce_list_of_dicts(image_output.get("image_sequence"))
    image_errors = [
        item
        for item in _coerce_list_of_dicts(pipeline_result.get("pipeline_errors"))
        if str(item.get("stage", "")).strip() == "image_generator"
    ]

    if image_status == "error":
        image_message = (
            str(image_errors[0].get("message")).strip()
            if image_errors
            else "Image generation failed."
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=image_message,
        )

    if not generated_images:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ImageGeneratorAgent completed without generating any images.",
        )

    return GenerateListingResponse(
        pipeline_status=str(pipeline_result.get("status", "error")),
        transcript=intake_result.transcript,
        cleaned_input=intake_result.cleaned,
        product_title=_coerce_str(
            copywriter_output.get("product_title") or intake_result.cleaned.product_title
        ),
        product_description=_coerce_str(
            copywriter_output.get("product_description")
            or intake_result.cleaned.cleaned_product_description
        ),
        images=generated_images,
        scene_descriptions=_coerce_list_of_dicts(studio_output.get("scene_descriptions")),
        video_script=_coerce_str(studio_output.get("ad_script")),
        upload_ready_data=_coerce_dict(pipeline_result.get("upload_package")),
        ready_for_upload=bool(pipeline_result.get("ready_for_upload", False)),
        stage_logs=_coerce_list_of_dicts(pipeline_result.get("stage_logs")),
        pipeline_errors=_coerce_list_of_dicts(pipeline_result.get("pipeline_errors")),
    )


def _build_pipeline_payload(
    *,
    intake_result: ProductIntakeResponse,
    image_bytes: bytes,
    image_content_type: str | None,
    image_filename: str,
    original_text: str | None,
    simulated_confirmation_response: str,
) -> dict[str, object]:
    return {
        "text": original_text or intake_result.combined_user_input,
        "voice_transcript": intake_result.transcript or "",
        "image_bytes": image_bytes,
        "image_content_type": image_content_type,
        "image_filename": image_filename,
        "image_notes": intake_result.cleaned.short_summary,
        "product_name": intake_result.cleaned.product_title,
        "product_title": intake_result.cleaned.product_title,
        "product_category": intake_result.cleaned.inferred_category,
        "product_description": intake_result.cleaned.cleaned_product_description,
        "bullet_highlights": intake_result.cleaned.key_features,
        "seo_tags": [],
        "input_summary": intake_result.cleaned.user_intent_summary,
        "simulated_confirmation_response": simulated_confirmation_response,
    }


def _coerce_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _coerce_list_of_dicts(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    output: list[dict[str, object]] = []
    for item in value:
        if isinstance(item, dict):
            output.append({str(key): subitem for key, subitem in item.items()})
    return output
