from app.agents.base import AgentPayload, BaseAgent
from app.schemas.agent import AgentResponse
from app.services.visionary_service import VisionaryService


class VisionaryAgent(BaseAgent):
    """Uses GPT-4o to interpret an uploaded product image."""

    name = "visionary"

    def __init__(self, visionary_service: VisionaryService | None = None) -> None:
        self.visionary_service = visionary_service or VisionaryService()

    async def run(self, payload: AgentPayload) -> AgentResponse:
        raw_image_bytes = payload.get("image_bytes")
        image_bytes = bytes(raw_image_bytes) if isinstance(raw_image_bytes, (bytes, bytearray)) else b""
        image_content_type = str(payload.get("image_content_type", "")).strip() or None
        image_filename = str(payload.get("image_filename", "")).strip() or None
        image_notes = str(payload.get("image_notes", "")).strip() or None

        if not image_bytes:
            return self.build_response(
                payload,
                {
                    "image_filename": image_filename,
                    "product_category": None,
                    "fabric": None,
                    "color": None,
                    "pattern": None,
                    "descriptive_paragraph": "No uploaded image was provided for analysis.",
                    "model_used": self.visionary_service.model,
                },
                status="invalid",
            )

        analysis = await self.visionary_service.analyze_product_image(
            image_bytes=image_bytes,
            image_content_type=image_content_type,
            image_notes=image_notes,
        )

        output = {
            "image_filename": image_filename,
            "product_category": analysis.category,
            "fabric": analysis.fabric,
            "color": analysis.color,
            "pattern": analysis.pattern,
            "descriptive_paragraph": analysis.descriptive_paragraph,
            "visual_summary": analysis.descriptive_paragraph,
            "model_used": self.visionary_service.model,
        }
        return self.build_response(payload, output)
