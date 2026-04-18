import re

from app.agents.base import AgentPayload, BaseAgent
from app.schemas.agent import AgentResponse


class RegistrarAgent(BaseAgent):
    """Validates listing data, simulates confirmation, and prepares upload payloads."""

    name = "registrar"

    async def run(self, payload: AgentPayload) -> AgentResponse:
        product_name = str(payload.get("product_name", "")).strip()
        product_title = str(payload.get("product_title", "")).strip()
        product_description = str(payload.get("product_description", "")).strip()
        bullet_highlights = payload.get("bullet_highlights", []) or []
        seo_tags = payload.get("seo_tags", []) or payload.get("seo_keywords", []) or []
        marketing_assets = payload.get("marketing_assets", {}) or {}
        simulated_confirmation_response = str(
            payload.get("simulated_confirmation_response", "approved")
        ).strip().lower() or "approved"

        errors: list[str] = []
        if not product_name:
            errors.append("product_name is required")
        if not product_title:
            errors.append("product_title is required")
        if not product_description:
            errors.append("product_description is required")
        if not isinstance(bullet_highlights, list) or not [
            item for item in bullet_highlights if str(item).strip()
        ]:
            errors.append("bullet_highlights must contain at least one highlight")
        if not isinstance(seo_tags, list) or not [item for item in seo_tags if str(item).strip()]:
            errors.append("seo_tags must contain at least one tag")
        if not marketing_assets:
            errors.append("marketing_assets are required")

        slug = self._slugify(product_name) if product_name else None
        confirmation = self._simulate_confirmation(simulated_confirmation_response, errors)
        upload_payload = self._build_upload_payload(
            payload=payload,
            slug=slug,
            product_name=product_name,
            product_title=product_title,
            product_description=product_description,
            bullet_highlights=bullet_highlights,
            seo_tags=seo_tags,
            marketing_assets=marketing_assets,
        )

        output = {
            "ready_for_upload": not errors and confirmation["confirmed"],
            "validation_errors": errors,
            "confirmation": confirmation,
            "upload_package": upload_payload,
            "mock_api_integration": {
                "provider": "mock-ondc",
                "integration_mode": "simulation",
                "request_ready": not errors and confirmation["confirmed"],
                "submission_status": self._resolve_submission_status(
                    confirmed=confirmation["confirmed"],
                    has_errors=bool(errors),
                ),
                "message": self._build_submission_message(
                    confirmed=confirmation["confirmed"],
                    has_errors=bool(errors),
                ),
                "endpoint": "/mock/ondc/catalog/upload",
            },
        }
        status = self._resolve_status(
            confirmed=confirmation["confirmed"],
            has_errors=bool(errors),
        )
        return self.build_response(payload, output, status=status)

    def _slugify(self, value: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return re.sub(r"-{2,}", "-", normalized)

    def _simulate_confirmation(
        self, response: str, validation_errors: list[str]
    ) -> dict[str, object]:
        normalized = response if response in {"approved", "rejected"} else "approved"
        if validation_errors:
            normalized = "rejected"

        return {
            "mode": "simulated",
            "requested": True,
            "response": normalized,
            "confirmed": normalized == "approved",
            "message": (
                "Simulated confirmation approved for upload."
                if normalized == "approved"
                else "Simulated confirmation rejected. Review the generated data before upload."
            ),
        }

    def _build_upload_payload(
        self,
        *,
        payload: AgentPayload,
        slug: str | None,
        product_name: str,
        product_title: str,
        product_description: str,
        bullet_highlights: list[object],
        seo_tags: list[object],
        marketing_assets: dict[object, object],
    ) -> dict[str, object]:
        clean_highlights = [str(item).strip() for item in bullet_highlights if str(item).strip()]
        clean_tags = [str(item).strip() for item in seo_tags if str(item).strip()]

        return {
            "sku_slug": slug,
            "product": {
                "name": product_name,
                "title": product_title,
                "description": product_description,
                "category": payload.get("product_category"),
                "fabric": payload.get("fabric"),
                "color": payload.get("color"),
                "pattern": payload.get("pattern"),
                "highlights": clean_highlights,
                "seo_tags": clean_tags,
            },
            "brand_story": {
                "background_context": payload.get("background_context"),
                "wikipedia_title": payload.get("wikipedia_title"),
                "wikipedia_url": payload.get("wikipedia_url"),
                "tone": payload.get("tone"),
            },
            "media": {
                "marketing_assets": marketing_assets,
                "image_sequence": payload.get("image_sequence", []),
                "stitching_plan": payload.get("stitching_plan", {}),
            },
            "catalog_metadata": {
                "source": "storyloom-agent-pipeline",
                "confirmation_mode": "simulated",
                "language": payload.get("language", "en"),
            },
        }

    def _resolve_status(self, *, confirmed: bool, has_errors: bool) -> str:
        if has_errors:
            return "invalid"
        if not confirmed:
            return "partial"
        return "success"

    def _resolve_submission_status(self, *, confirmed: bool, has_errors: bool) -> str:
        if has_errors:
            return "blocked_validation_failed"
        if not confirmed:
            return "blocked_confirmation_required"
        return "ready_for_mock_upload"

    def _build_submission_message(self, *, confirmed: bool, has_errors: bool) -> str:
        if has_errors:
            return "Mock upload blocked because validation failed."
        if not confirmed:
            return "Mock upload blocked because the simulated confirmation was rejected."
        return "Mock upload payload prepared successfully. No real ONDC API call was made."
