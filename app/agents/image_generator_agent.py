from app.agents.base import AgentPayload, BaseAgent
from app.schemas.agent import AgentResponse
from app.services.product_image_service import ProductImageService


class ImageGeneratorAgent(BaseAgent):
    """Generates 3 clear, professional marketing images from the uploaded source photo."""

    name = "image_generator"

    def __init__(
        self, product_image_service: ProductImageService | None = None
    ) -> None:
        self.product_image_service = product_image_service or ProductImageService()

    async def run(self, payload: AgentPayload) -> AgentResponse:
        raw_image_bytes = payload.get("image_bytes")
        image_bytes = (
            bytes(raw_image_bytes)
            if isinstance(raw_image_bytes, (bytes, bytearray))
            else b""
        )
        if not image_bytes:
            raise ValueError("ImageGeneratorAgent requires `image_bytes`.")

        product_title = str(
            payload.get("product_title") or payload.get("product_name") or "Product"
        ).strip()
        result = await self.product_image_service.generate_product_images(
            product_title=product_title,
            product_description=str(payload.get("product_description", "")).strip(),
            product_category=str(payload.get("product_category", "product")).strip()
            or "product",
            fabric=str(payload.get("fabric", "")).strip(),
            color=str(payload.get("color", "")).strip(),
            pattern=str(payload.get("pattern", "")).strip(),
            scene_descriptions=payload.get("scene_descriptions", []) or [],
            source_image_bytes=image_bytes,
            source_image_filename=str(payload.get("image_filename", "")).strip() or None,
            source_image_content_type=str(payload.get("image_content_type", "")).strip()
            or None,
        )

        marketing_assets = dict(payload.get("marketing_assets", {}) or {})
        marketing_assets["image_sequence"] = result["image_sequence"]
        marketing_assets["image_generation_summary"] = result["image_generation_summary"]

        output = {
            "marketing_assets": marketing_assets,
            "image_sequence": result["image_sequence"],
            "image_generation_summary": result["image_generation_summary"],
        }
        return self.build_response(payload, output)
