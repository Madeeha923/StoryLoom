from pydantic import BaseModel, Field


class CleanedProductDescription(BaseModel):
    product_title: str
    inferred_category: str
    cleaned_product_description: str
    short_summary: str
    key_features: list[str] = Field(default_factory=list)
    user_intent_summary: str


class ProductIntakeResponse(BaseModel):
    transcript: str | None = None
    combined_user_input: str
    cleaned: CleanedProductDescription
    image_filename: str
    audio_filename: str | None = None
    model_used_for_cleanup: str
    model_used_for_transcription: str | None = None

