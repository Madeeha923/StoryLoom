import base64
import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.visionary import VisionaryAnalysis
from app.services.openai_client import get_async_openai_client


class VisionaryService:
    """Uses GPT-4o to extract visual product details from an uploaded image."""

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self.client = client or get_async_openai_client()
        self.model = settings.openai_vision_model

    async def analyze_product_image(
        self,
        *,
        image_bytes: bytes,
        image_content_type: str | None,
        image_notes: str | None = None,
    ) -> VisionaryAnalysis:
        image_data_url = self._to_data_url(
            payload=image_bytes,
            content_type=image_content_type or "image/jpeg",
        )
        response = await self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": self._build_prompt(image_notes=image_notes),
                        },
                        {
                            "type": "input_image",
                            "image_url": image_data_url,
                            "detail": "high",
                        },
                    ],
                }
            ],
            temperature=0.1,
            max_output_tokens=500,
        )
        payload = self._parse_json_response(response.output_text)
        return VisionaryAnalysis.model_validate(payload)

    def _build_prompt(self, *, image_notes: str | None) -> str:
        return (
            "You are a fashion and e-commerce visual analyst.\n"
            "Analyze the uploaded product image and extract grounded product details.\n"
            "Return JSON only using this exact schema:\n"
            "{\n"
            '  "category": "string",\n'
            '  "fabric": "string",\n'
            '  "color": "string",\n'
            '  "pattern": "string",\n'
            '  "descriptive_paragraph": "string"\n'
            "}\n"
            "Rules:\n"
            "- Base the answer only on what is visible in the image and any optional notes.\n"
            "- If fabric is uncertain, use cautious wording such as 'fabric not clearly identifiable; appears cotton-like'.\n"
            "- Keep the descriptive paragraph concise, natural, and catalog-friendly.\n"
            f"Optional notes: {image_notes or 'None provided'}"
        )

    def _to_data_url(self, *, payload: bytes, content_type: str) -> str:
        encoded = base64.b64encode(payload).decode("utf-8")
        return f"data:{content_type};base64,{encoded}"

    def _parse_json_response(self, raw_output: str) -> dict[str, Any]:
        candidate = raw_output.strip()
        if candidate.startswith("```"):
            lines = candidate.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            candidate = "\n".join(lines).strip()
            if candidate.lower().startswith("json"):
                candidate = candidate[4:].strip()

        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Visionary model returned invalid JSON: {exc}") from exc

