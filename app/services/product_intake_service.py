import base64
import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.product_intake import (
    CleanedProductDescription,
    ProductIntakeResponse,
)
from app.services.openai_client import get_async_openai_client


class ProductIntakeService:
    """Handles audio transcription and multimodal product-description cleanup."""

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self.client = client or get_async_openai_client()
        self.transcription_model = settings.openai_transcription_model
        self.cleanup_model = settings.openai_cleanup_model

    async def process_uploads(
        self,
        *,
        image_bytes: bytes,
        image_filename: str,
        image_content_type: str | None,
        text_input: str | None,
        audio_bytes: bytes | None,
        audio_filename: str | None,
        audio_content_type: str | None,
    ) -> ProductIntakeResponse:
        transcript: str | None = None
        if audio_bytes and audio_filename:
            transcript = await self.transcribe_audio(
                audio_bytes=audio_bytes,
                audio_filename=audio_filename,
                audio_content_type=audio_content_type,
            )

        combined_user_input = self._combine_inputs(text_input=text_input, transcript=transcript)
        cleaned = await self.clean_product_description(
            image_bytes=image_bytes,
            image_content_type=image_content_type,
            text_input=text_input,
            transcript=transcript,
            combined_user_input=combined_user_input,
        )

        return ProductIntakeResponse(
            transcript=transcript,
            combined_user_input=combined_user_input,
            cleaned=cleaned,
            image_filename=image_filename,
            audio_filename=audio_filename,
            model_used_for_cleanup=self.cleanup_model,
            model_used_for_transcription=self.transcription_model if transcript else None,
        )

    async def transcribe_audio(
        self,
        *,
        audio_bytes: bytes,
        audio_filename: str,
        audio_content_type: str | None,
    ) -> str:
        transcription = await self.client.audio.transcriptions.create(
            model=self.transcription_model,
            file=(audio_filename, audio_bytes, audio_content_type or "application/octet-stream"),
            response_format="text",
            prompt=(
                "This audio contains a shopper or seller describing a product for an "
                "e-commerce listing. Preserve product names, materials, sizes, colors, "
                "and notable brand or cultural references accurately."
            ),
        )
        return transcription if isinstance(transcription, str) else transcription.text

    async def clean_product_description(
        self,
        *,
        image_bytes: bytes,
        image_content_type: str | None,
        text_input: str | None,
        transcript: str | None,
        combined_user_input: str,
    ) -> CleanedProductDescription:
        image_data_url = self._to_data_url(
            payload=image_bytes,
            content_type=image_content_type or "image/jpeg",
        )
        response = await self.client.responses.create(
            model=self.cleanup_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": self._build_cleanup_prompt(
                                text_input=text_input,
                                transcript=transcript,
                                combined_user_input=combined_user_input,
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": image_data_url,
                            "detail": "high",
                        },
                    ],
                }
            ],
            temperature=0.2,
            max_output_tokens=700,
        )

        cleaned_payload = self._parse_json_response(response.output_text)
        return CleanedProductDescription.model_validate(cleaned_payload)

    def _combine_inputs(self, *, text_input: str | None, transcript: str | None) -> str:
        parts = [part.strip() for part in [text_input or "", transcript or ""] if part and part.strip()]
        return "\n".join(parts) if parts else "No text or audio details were supplied. Infer only conservative product details from the image."

    def _build_cleanup_prompt(
        self,
        *,
        text_input: str | None,
        transcript: str | None,
        combined_user_input: str,
    ) -> str:
        return (
            "You are preparing structured product copy for an e-commerce catalog.\n"
            "Use the uploaded product image plus the user inputs below.\n"
            "Rewrite the messy request into clean, usable product information.\n"
            "Be visually grounded: do not invent details that are not visible or stated.\n"
            "If uncertain, use cautious wording.\n"
            "Return JSON only with this exact schema:\n"
            "{\n"
            '  "product_title": "string",\n'
            '  "inferred_category": "string",\n'
            '  "cleaned_product_description": "string",\n'
            '  "short_summary": "string",\n'
            '  "key_features": ["string"],\n'
            '  "user_intent_summary": "string"\n'
            "}\n\n"
            f"Raw text input: {text_input or 'None provided'}\n"
            f"Voice transcript: {transcript or 'None provided'}\n"
            f"Combined user input: {combined_user_input}"
        )

    def _to_data_url(self, *, payload: bytes, content_type: str) -> str:
        encoded = base64.b64encode(payload).decode("utf-8")
        return f"data:{content_type};base64,{encoded}"

    def _parse_json_response(self, raw_output: str) -> dict[str, Any]:
        candidate = raw_output.strip()
        if candidate.startswith("```"):
            candidate = candidate.strip("`")
            if candidate.lower().startswith("json"):
                candidate = candidate[4:].strip()

        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Model returned invalid JSON: {exc}") from exc


def get_product_intake_service() -> ProductIntakeService:
    return ProductIntakeService()

