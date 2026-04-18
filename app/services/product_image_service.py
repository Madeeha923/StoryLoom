import base64
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.openai_client import get_async_openai_client

logger = logging.getLogger(__name__)
GENERATED_IMAGES_DIR = Path("generated") / "images"
GENERATED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


class ProductImageService:
    """Generates clean, sale-ready product images from the uploaded source photo."""

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self.client = client or get_async_openai_client()
        self.image_model = (
            settings.openai_product_image_model
            or settings.openai_studio_image_model
        )

    async def generate_product_images(
        self,
        *,
        product_title: str,
        product_description: str,
        product_category: str,
        fabric: str,
        color: str,
        pattern: str,
        scene_descriptions: list[dict[str, Any]] | None,
        source_image_bytes: bytes,
        source_image_filename: str | None,
        source_image_content_type: str | None,
    ) -> dict[str, Any]:
        image_jobs = self._build_image_jobs(
            product_title=product_title,
            product_description=product_description,
            product_category=product_category,
            fabric=fabric,
            color=color,
            pattern=pattern,
            scene_descriptions=scene_descriptions or [],
        )

        image_sequence: list[dict[str, Any]] = []
        for job in image_jobs:
            logger.info(
                "ImageGeneratorAgent started scene %s ('%s')",
                job["scene_number"],
                job["scene_title"],
            )
            image_result = await self._create_image(
                prompt=str(job["frame_prompt"]),
                scene_title=str(job["scene_title"]),
                source_image_bytes=source_image_bytes,
                source_image_filename=source_image_filename,
                source_image_content_type=source_image_content_type,
            )
            image_sequence.append(
                {
                    "scene_number": job["scene_number"],
                    "scene_title": job["scene_title"],
                    "duration_seconds": job["duration_seconds"],
                    "scene_description": job["scene_description"],
                    "frame_prompt": job["frame_prompt"],
                    "transition_note": job["transition_note"],
                    "frame_image_b64": image_result["frame_image_b64"],
                    "revised_prompt": image_result["revised_prompt"],
                    "output_format": image_result["output_format"],
                    "size": image_result["size"],
                    "quality": image_result["quality"],
                    "generation_model": image_result["generation_model"],
                    "generation_method": image_result["generation_method"],
                    "source_image_used": image_result["source_image_used"],
                    "image_url": image_result["image_url"],
                    "image_filename": image_result["image_filename"],
                }
            )
            logger.info(
                "ImageGeneratorAgent completed scene %s using '%s' via '%s'",
                job["scene_number"],
                image_result["generation_model"],
                image_result["generation_method"],
            )

        return {
            "image_sequence": image_sequence,
            "image_generation_summary": {
                "model": self.image_model,
                "images_requested": len(image_jobs),
                "images_generated": len(image_sequence),
                "instruction": (
                    "Generate 3 clear, professional, product-preserving marketing images "
                    "from the uploaded source photo."
                ),
            },
        }

    async def _create_image(
        self,
        *,
        prompt: str,
        scene_title: str,
        source_image_bytes: bytes,
        source_image_filename: str | None,
        source_image_content_type: str | None,
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        candidate_models = self._candidate_models()

        for model_name in candidate_models:
            try:
                logger.info(
                    "Trying product image edit for scene '%s' with model '%s'",
                    scene_title,
                    model_name,
                )
                image_response = await self.client.images.edit(
                    model=model_name,
                    image=(
                        source_image_filename or "product-source.jpg",
                        source_image_bytes,
                        source_image_content_type or "image/jpeg",
                    ),
                    prompt=prompt,
                    input_fidelity="high",
                    quality="high",
                    size="1536x1024",
                    output_format="png",
                    n=1,
                )
                return self._serialize_image_response(
                    image_response=image_response,
                    generation_model=model_name,
                    generation_method="edit",
                    source_image_used=True,
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Product image edit failed for scene '%s' with model '%s': %s",
                    scene_title,
                    model_name,
                    exc,
                )

            try:
                logger.info(
                    "Trying product image generation for scene '%s' with model '%s'",
                    scene_title,
                    model_name,
                )
                image_response = await self.client.images.generate(
                    model=model_name,
                    prompt=prompt,
                    quality="high",
                    size="1536x1024",
                    output_format="png",
                    n=1,
                )
                return self._serialize_image_response(
                    image_response=image_response,
                    generation_model=model_name,
                    generation_method="generate",
                    source_image_used=False,
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Product image generation failed for scene '%s' with model '%s': %s",
                    scene_title,
                    model_name,
                    exc,
                )

        raise ValueError(
            "Product image generation failed for all candidate image models: "
            f"{last_error}"
        )

    def _serialize_image_response(
        self,
        *,
        image_response: Any,
        generation_model: str,
        generation_method: str,
        source_image_used: bool,
    ) -> dict[str, Any]:
        image_data = (image_response.data or [None])[0]
        if image_data is None or not getattr(image_data, "b64_json", None):
            raise ValueError("Image API returned no base64 image payload.")

        output_format = image_response.output_format or "png"
        image_filename = self._save_generated_image(
            image_b64=str(image_data.b64_json),
            scene_slug=generation_method,
            output_format=output_format,
        )

        return {
            "frame_image_b64": image_data.b64_json,
            "revised_prompt": getattr(image_data, "revised_prompt", None),
            "output_format": output_format,
            "size": image_response.size or "1536x1024",
            "quality": image_response.quality or "high",
            "generation_model": generation_model,
            "generation_method": generation_method,
            "source_image_used": source_image_used,
            "image_url": f"/generated/images/{image_filename}",
            "image_filename": image_filename,
        }

    def _build_image_jobs(
        self,
        *,
        product_title: str,
        product_description: str,
        product_category: str,
        fabric: str,
        color: str,
        pattern: str,
        scene_descriptions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        scenes = scene_descriptions[:3] if scene_descriptions else []
        defaults = [
            {
                "scene_number": 1,
                "scene_title": "Hero Product Shot",
                "duration_seconds": 4,
                "scene_description": "A clean ecommerce hero image with the full product clearly visible.",
                "transition_note": "Lead with the clearest sellable product shot.",
                "scene_direction": "Use a premium studio setup and keep the full product clearly visible.",
            },
            {
                "scene_number": 2,
                "scene_title": "Material Detail Close-Up",
                "duration_seconds": 4,
                "scene_description": "A crisp close-up focused on craftsmanship, texture, and material quality.",
                "transition_note": "Highlight detail and quality.",
                "scene_direction": "Zoom into fabric, texture, finish, and craftsmanship while keeping the product realistic.",
            },
            {
                "scene_number": 3,
                "scene_title": "Lifestyle Sales Frame",
                "duration_seconds": 4,
                "scene_description": "A tasteful lifestyle frame where the product remains the hero subject.",
                "transition_note": "Close with aspiration while keeping the product dominant.",
                "scene_direction": "Add subtle premium context, but keep the product large, realistic, and sale-ready.",
            },
        ]

        jobs: list[dict[str, Any]] = []
        for index, fallback in enumerate(defaults):
            scene = scenes[index] if index < len(scenes) else {}
            scene_number = int(scene.get("scene_number", fallback["scene_number"]))
            scene_title = str(scene.get("scene_title", fallback["scene_title"]))
            scene_description = str(
                scene.get("scene_description", fallback["scene_description"])
            )
            transition_note = str(
                scene.get("transition_note", fallback["transition_note"])
            )
            direction = str(
                scene.get("frame_prompt")
                or scene.get("scene_direction")
                or fallback["scene_direction"]
            )
            jobs.append(
                {
                    "scene_number": scene_number,
                    "scene_title": scene_title,
                    "duration_seconds": int(
                        scene.get("duration_seconds", fallback["duration_seconds"])
                    ),
                    "scene_description": scene_description,
                    "transition_note": transition_note,
                    "frame_prompt": self._build_generation_prompt(
                        product_title=product_title,
                        product_description=product_description,
                        product_category=product_category,
                        fabric=fabric,
                        color=color,
                        pattern=pattern,
                        scene_title=scene_title,
                        scene_direction=direction,
                    ),
                }
            )
        return jobs

    def _build_generation_prompt(
        self,
        *,
        product_title: str,
        product_description: str,
        product_category: str,
        fabric: str,
        color: str,
        pattern: str,
        scene_title: str,
        scene_direction: str,
    ) -> str:
        return (
            "Generate a clear, realistic, professional ecommerce product image based on the uploaded source photo. "
            "This must be the exact same product, not a different interpretation. "
            "Preserve the same product identity, shape, silhouette, construction, material feel, color accuracy, pattern, and proportions. "
            "Make the product the hero and keep it fully visible or clearly readable in frame. "
            "The result must look like a polished commercial catalog photo, suitable for selling online. "
            "Do not return a blank white frame. Do not return abstract colors. Do not hide the product. "
            "Do not invent text overlays, watermarks, mannequins, or distracting props unless the scene explicitly calls for subtle context.\n"
            f"Product title: {product_title}\n"
            f"Product category: {product_category}\n"
            f"Product description: {product_description[:400]}\n"
            f"Fabric: {fabric or 'not specified'}\n"
            f"Color: {color or 'not specified'}\n"
            f"Pattern: {pattern or 'not specified'}\n"
            f"Scene title: {scene_title}\n"
            f"Scene direction: {scene_direction}\n"
            "Instruction: generate one professional sale-ready image for this scene."
        )

    def _candidate_models(self) -> list[str]:
        candidates = [
            self.image_model,
            settings.openai_studio_image_model,
            "gpt-image-1.5",
            "gpt-image-1",
            "gpt-image-1-mini",
        ]
        deduped: list[str] = []
        for candidate in candidates:
            if candidate and candidate not in deduped:
                deduped.append(candidate)
        return deduped

    def _save_generated_image(
        self,
        *,
        image_b64: str,
        scene_slug: str,
        output_format: str,
    ) -> str:
        safe_extension = output_format if output_format in {"png", "jpeg", "webp"} else "png"
        filename = f"{scene_slug}-{uuid4().hex}.{safe_extension}"
        image_path = GENERATED_IMAGES_DIR / filename
        image_path.write_bytes(base64.b64decode(image_b64))
        return filename
