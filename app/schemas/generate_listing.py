from typing import Any

from pydantic import BaseModel, Field

from app.schemas.product_intake import CleanedProductDescription


class GenerateListingResponse(BaseModel):
    pipeline_status: str
    transcript: str | None = None
    cleaned_input: CleanedProductDescription
    product_title: str | None = None
    product_description: str | None = None
    images: list[dict[str, Any]] = Field(default_factory=list)
    scene_descriptions: list[dict[str, Any]] = Field(default_factory=list)
    video_script: str | None = None
    upload_ready_data: dict[str, Any] = Field(default_factory=dict)
    ready_for_upload: bool = False
    stage_logs: list[dict[str, Any]] = Field(default_factory=list)
    pipeline_errors: list[dict[str, Any]] = Field(default_factory=list)

