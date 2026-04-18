from app.agents.base import AgentPayload, BaseAgent
from app.schemas.agent import AgentResponse
from app.services.studio_service import StudioService


class StudioAgent(BaseAgent):
    """Generates campaign planning, ad script, and scene directions."""

    name = "studio"

    def __init__(self, studio_service: StudioService | None = None) -> None:
        self.studio_service = studio_service or StudioService()

    async def run(self, payload: AgentPayload) -> AgentResponse:
        product_title = str(payload.get("product_title", "")).strip() or str(
            payload.get("product_name", "Unnamed Product")
        ).strip()
        description = str(payload.get("product_description", "")).strip()
        bullet_highlights = payload.get("bullet_highlights", []) or []
        highlights = (
            [str(item).strip() for item in bullet_highlights if str(item).strip()]
            if isinstance(bullet_highlights, list)
            else []
        )
        seo_tags = payload.get("seo_tags", []) or payload.get("seo_keywords", []) or []
        normalized_tags = (
            [str(item).strip() for item in seo_tags if str(item).strip()]
            if isinstance(seo_tags, list)
            else []
        )
        visual_summary = str(payload.get("visual_summary", "")).strip()
        background_context = str(payload.get("background_context", "")).strip()
        product_category = str(payload.get("product_category", "product")).strip() or "product"
        fabric = str(payload.get("fabric", "")).strip()
        color = str(payload.get("color", "")).strip()
        pattern = str(payload.get("pattern", "")).strip()
        raw_image_bytes = payload.get("image_bytes")
        image_bytes = bytes(raw_image_bytes) if isinstance(raw_image_bytes, (bytes, bytearray)) else None
        image_content_type = str(payload.get("image_content_type", "")).strip() or None

        campaign_assets = await self.studio_service.create_campaign_assets(
            product_title=product_title,
            product_description=description,
            bullet_highlights=highlights,
            seo_tags=normalized_tags,
            background_context=background_context,
            visual_summary=visual_summary,
            product_category=product_category,
            fabric=fabric,
            color=color,
            pattern=pattern,
            source_image_bytes=image_bytes,
            source_image_content_type=image_content_type,
        )

        output = {
            "marketing_assets": campaign_assets,
            "ad_script": campaign_assets["ad_script"],
            "scene_descriptions": campaign_assets["scene_descriptions"],
            "image_sequence": campaign_assets["image_sequence"],
            "stitching_plan": campaign_assets["stitching_plan"],
            "studio_models": {
                "planning_model": self.studio_service.planning_model,
            },
        }
        return self.build_response(payload, output)
